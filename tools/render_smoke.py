"""Render a synthetic block scene through the shipped shader pipeline on a real GPU.

These are engineering fixtures, not Minecraft screenshots or in-game acceptance.
"""
import ctypes as C
import json
import math
import numpy as np
from PIL import Image, ImageDraw
from build import ROOT, SHADERS, PROFILE_KEYS, PROFILES, shader_digest
from validate import source_for
from gl_context import GLContext

U=C.c_uint; I=C.c_int; F=C.c_float; P=C.c_void_p

def normalized(v):
    v=np.asarray(v,dtype=np.float32)
    return v/max(np.linalg.norm(v),1e-8)

def look_at(eye, target):
    f=normalized(np.asarray(target)-eye); s=normalized(np.cross(f,[0,1,0])); u=np.cross(s,f)
    m=np.eye(4,dtype=np.float32); m[:3,:3]=[s,u,-f]; m[:3,3]=-m[:3,:3]@eye
    return m

def perspective(aspect):
    n,f=0.05,512.0; scale=1/math.tan(math.radians(64)/2)
    m=np.zeros((4,4),dtype=np.float32)
    m[0,0]=scale/aspect; m[1,1]=scale; m[2,2]=-(f+n)/(f-n)
    m[2,3]=-2*f*n/(f-n); m[3,2]=-1
    return m

class Renderer:
    def __init__(self,width=640,height=360):
        self.gl=GLContext(); self.w=width; self.h=height; self.textures=[]; self.programs={}
        callback_type=C.WINFUNCTYPE(None,U,U,U,U,I,C.c_char_p,P)
        self.debug_callback=callback_type(lambda source,kind,ident,severity,length,message,user: print(message.decode(),flush=True) if kind==0x824C else None)
        self.gl.fn('glDebugMessageCallback',None,callback_type,P)(self.debug_callback,None)
        self.gl.fn('glEnable',None,U)(0x92E0)
        self.gl.fn('glEnable',None,U)(0x8242)
        # WGL procedure lookup can flush; resolve immediate-mode calls before glBegin.
        for name,args in [('glBegin',[U]),('glEnd',[]),('glVertex3f',[F,F,F]),('glMultiTexCoord2f',[U,F,F])]:
            self.gl.fn(name,None,*args)
        self.fbo=U(); self.gl.fn('glGenFramebuffers',None,I,C.POINTER(U))(1,C.byref(self.fbo))
        self.projection=perspective(width/height)
        self.camera=np.array([12,72,18],dtype=np.float32)
        look=look_at(self.camera,np.array([0,65,0],dtype=np.float32))
        self.rotation=look.copy(); self.rotation[:3,3]=0
        self.translation=np.eye(4,dtype=np.float32); self.translation[:3,3]=-self.camera
        self.white=self.texture(1,1,data=np.ones((1,1,4),np.float32))
        pattern=np.ones((16,16,4),np.float32)
        y,x=np.mgrid[0:16,0:16]; pattern[:,:,:3]*=(0.83+0.17*((x+y)%2))[:,:,None]
        self.checker=self.texture(16,16,data=pattern)
        self.normal=self.texture(1,1,data=np.array([[[0.5,0.5,1,1]]],np.float32))
        self.spec=self.texture(1,1,data=np.array([[[0,0.04,0,1]]],np.float32))
        self.shadow_depth=self.texture(2048,2048,depth=True)
        self.shadow_color=self.texture(2048,2048)
        self.depth=self.texture(width,height,depth=True)
        self.opaque_depth=self.texture(width,height,depth=True)
        self.buffers={i:self.texture(width//4 if i in [5,6] else width,height//4 if i in [5,6] else height,internal_format=0x8C3A if i in [5,6] else 0x8058 if i==3 else 0x881A) for i in range(7)}
        self.spare={i:self.texture(width//4 if i in [5,6] else width,height//4 if i in [5,6] else height,internal_format=0x8C3A if i in [5,6] else 0x8058 if i==3 else 0x881A) for i in range(7)}
        self.final=self.texture(width,height)

    def call(self,name,result,args,*values): return self.gl.fn(name,result,*args)(*values)

    def check(self,stage):
        error=self.call('glGetError',U,[])
        assert error==0,f'{stage}: OpenGL error {error:x}'

    def texture(self,w,h,data=None,depth=False,internal_format=0x881A):
        tex=U(); self.call('glGenTextures',None,[I,C.POINTER(U)],1,C.byref(tex))
        self.call('glBindTexture',None,[U,U],0x0DE1,tex.value)
        for pname,value in [(0x2801,0x2600 if depth else 0x2601),(0x2800,0x2600 if depth else 0x2601),(0x2802,0x812F),(0x2803,0x812F)]:
            self.call('glTexParameteri',None,[U,U,I],0x0DE1,pname,value)
        self.call('glTexImage2D',None,[U,I,I,I,I,I,U,U,P],0x0DE1,0,0x8CAC if depth else internal_format,w,h,0,0x1902 if depth else 0x1908,0x1406,None if data is None else data.ctypes.data)
        self.textures.append(tex.value)
        return tex.value

    def bind_fbo(self,outputs,depth=0,w=None,h=None):
        self.call('glBindFramebuffer',None,[U,U],0x8D40,self.fbo.value)
        for i in range(4):
            self.call('glFramebufferTexture2D',None,[U,U,U,U,I],0x8D40,0x8CE0+i,0x0DE1,outputs[i] if i<len(outputs) else 0,0)
        self.call('glFramebufferTexture2D',None,[U,U,U,U,I],0x8D40,0x8D00,0x0DE1,depth,0)
        values=(U*len(outputs))(*[0x8CE0+i for i in range(len(outputs))])
        self.call('glDrawBuffers',None,[I,C.POINTER(U)],len(values),values)
        status=self.call('glCheckFramebufferStatus',U,[U],0x8D40)
        assert status==0x8CD5,f'Framebuffer incomplete: {status:x}'
        self.call('glViewport',None,[I,I,I,I],0,0,w or self.w,h or self.h)

    def matrix(self,kind,value):
        self.call('glMatrixMode',None,[U],kind)
        array=np.ascontiguousarray(value.T,dtype=np.float32)
        self.call('glLoadMatrixf',None,[P],array.ctypes.data)

    def uniform(self,program,name,value):
        loc=self.call('glGetUniformLocation',I,[U,C.c_char_p],program,name.encode())
        if loc<0:return
        if isinstance(value,np.ndarray) and value.shape==(4,4):
            a=np.ascontiguousarray(value.T,dtype=np.float32)
            self.call('glUniformMatrix4fv',None,[I,I,C.c_ubyte,P],loc,1,0,a.ctypes.data)
        elif isinstance(value,int): self.call('glUniform1i',None,[I,I],loc,value)
        elif isinstance(value,(list,tuple,np.ndarray)):
            if name=='eyeBrightnessSmooth': self.call('glUniform2i',None,[I,I,I],loc,*map(int,value))
            else: self.call(f'glUniform{len(value)}f',None,[I]+[F]*len(value),loc,*map(float,value))
        else: self.call('glUniform1f',None,[I,F],loc,float(value))

    def use(self,name,folder,options):
        key=(name,folder,tuple(sorted(options.items())))
        if key not in self.programs:
            self.programs[key]=self.gl.compile(source_for(SHADERS/folder/(name+'.vsh'),options),source_for(SHADERS/folder/(name+'.fsh'),options))
        program=self.programs[key]
        self.call('glUseProgram',None,[U],program)
        for uniform,value in self.uniforms.items(): self.uniform(program,uniform,value)
        samplers={'texture':self.checker,'normals':self.normal,'specular':self.spec,'shadowtex0':self.shadow_depth,'depthtex0':self.depth,'depthtex1':self.opaque_depth,**{f'colortex{i}':t for i,t in self.buffers.items()}}
        for unit,(sampler,texture) in enumerate(samplers.items()):
            self.call('glActiveTexture',None,[U],0x84C0+unit)
            self.call('glBindTexture',None,[U,U],0x0DE1,texture)
            self.uniform(program,sampler,unit)
        self.call('glActiveTexture',None,[U],0x84C0)
        return program

    def quad(self,program,vertices,normal,color,block=0,sky=1.0,torch=0.0):
        for name,value in [('mc_Entity',[block,0,0,0]),('mc_midTexCoord',[0.5,0.5,0,0]),('at_tangent',[1,0,0,1])]:
            loc=self.call('glGetAttribLocation',I,[U,C.c_char_p],program,name.encode())
            if loc>=0: self.call('glVertexAttrib4f',None,[U,F,F,F,F],loc,*value)
        self.call('glColor4f',None,[F,F,F,F],*color,1.0)
        self.call('glNormal3f',None,[F,F,F],*normal)
        self.call('glBegin',None,[U],7)
        for uv,vertex in zip([(0,0),(1,0),(1,1),(0,1)],vertices):
            self.call('glMultiTexCoord2f',None,[U,F,F],0x84C0,*uv)
            self.call('glMultiTexCoord2f',None,[U,F,F],0x84C1,torch*240/256+8/256,sky*240/256+8/256)
            self.call('glVertex3f',None,[F,F,F],*vertex)
        self.call('glEnd',None,[])

    def box(self,p,center,size,color,block=0,sky=1,torch=0):
        x,y,z=center; a,b,c=np.asarray(size)/2
        faces=[([(-a,-b,c),(a,-b,c),(a,b,c),(-a,b,c)],(0,0,1)),
               ([(a,-b,-c),(-a,-b,-c),(-a,b,-c),(a,b,-c)],(0,0,-1)),
               ([(a,-b,c),(a,-b,-c),(a,b,-c),(a,b,c)],(1,0,0)),
               ([(-a,-b,-c),(-a,-b,c),(-a,b,c),(-a,b,-c)],(-1,0,0)),
               ([(-a,b,c),(a,b,c),(a,b,-c),(-a,b,-c)],(0,1,0)),
               ([(-a,-b,-c),(a,-b,-c),(a,-b,c),(-a,-b,c)],(0,-1,0))]
        for vertices,normal in faces:
            self.quad(p,[(vx+x,vy+y,vz+z) for vx,vy,vz in vertices],normal,color,block,sky,torch)

    def scene(self,program,kind):
        cave=kind=='cave'; sky=0.0 if cave else 1.0
        floor_color=(0.38,0.40,0.36) if cave else (0.37,0.48,0.27)
        self.box(program,(0,62.5,0),(42,1,42),floor_color,sky=sky,torch=0.12 if cave else 0)
        self.box(program,(-5,64,-1),(4,2,4),(0.73,0.63,0.43),sky=sky)
        self.box(program,(0,65,-3),(3,4,3),(0.59,0.23,0.17),sky=sky,torch=0.25 if cave else 0)
        self.box(program,(5,64.5,-1),(3,3,3),(0.68,0.70,0.71),sky=sky,torch=0.45 if cave else 0)
        self.box(program,(-2,64,4),(1,2,1),(0.95,0.63,0.22),10101,sky,0.9)
        self.box(program,(3,63.5,5),(0.8,1,0.8),(0.25,0.77,0.92),10102,sky,0.75)
        self.box(program,(-9,66,-6),(1.2,6,1.2),(0.38,0.26,0.15),sky=sky)
        self.box(program,(-9,69,-6),(6,3,5),(0.31,0.44,0.21),10002,sky)
        self.box(program,(3,63.2,-8),(4,0.3,3),(1.0,0.30,0.02),10103,sky,1.0)
        if cave:
            self.box(program,(0,72,-5),(32,2,26),(0.33,0.34,0.35),sky=0)
            self.box(program,(-16,67,-5),(2,10,26),(0.35,0.34,0.31),sky=0)
            self.box(program,(0,67,-18),(32,10,2),(0.35,0.34,0.31),sky=0)

    def full_screen(self):
        self.matrix(0x1701,np.eye(4)); self.matrix(0x1700,np.eye(4))
        self.call('glBegin',None,[U],7)
        for x,y in [(-1,-1),(1,-1),(1,1),(-1,1)]:
            self.call('glMultiTexCoord2f',None,[U,F,F],0x84C0,(x+1)*0.5,(y+1)*0.5)
            self.call('glVertex3f',None,[F,F,F],x,y,0)
        self.call('glEnd',None,[])

    def render(self,kind='day',profile='HIGH',options=None,time=25.0):
        self.check('initialization')
        folder={'nether':'world-1','end':'world1'}.get(kind,'world0')
        opts=dict(zip(PROFILE_KEYS,PROFILES[profile])); opts.update(options or {})
        sun=normalized([0.5,0.8,0.4])
        if kind=='sunset': sun=normalized([0.8,0.06,-0.2])
        if kind=='night':sun=-sun
        light=sun if sun[1]>=0 else -sun
        sm=look_at(light*128,np.zeros(3)); sp=np.eye(4,dtype=np.float32)
        sp[0,0]=sp[1,1]=1/128; sp[2,2]=-1/256
        self.uniforms={
            'gbufferModelView':self.rotation,'gbufferModelViewInverse':np.linalg.inv(self.rotation),
            'gbufferProjection':self.projection,'gbufferProjectionInverse':np.linalg.inv(self.projection),
            'gbufferPreviousModelView':self.rotation,'gbufferPreviousProjection':self.projection,
            'shadowModelView':sm,'shadowModelViewInverse':np.linalg.inv(sm),'shadowProjection':sp,
            'cameraPosition':self.camera,'previousCameraPosition':self.camera,
            'sunPosition':self.rotation[:3,:3]@sun*100,'moonPosition':self.rotation[:3,:3]@(-sun)*100,
            'shadowLightPosition':self.rotation[:3,:3]@light*100,
            'viewWidth':float(self.w),'viewHeight':float(self.h),'near':0.05,'far':128.0,
            'rainStrength':1.0 if kind in ['rain','thunder'] else 0.0,
            'wetness':1.0 if kind in ['rain','thunder'] else 0.0,
            'thunderStrength':1.0 if kind=='thunder' else 0.0,
            'frameTimeCounter':time,'isEyeInWater':1 if kind=='underwater' else 0,
            'moonPhase':4,'eyeBrightnessSmooth':[40,0 if kind in ['cave','nether','end'] else 240],
            'fogColor':[0.35,0.07,0.025] if kind=='nether' else [0.4,0.55,0.7],
            'skyColor':[0.4,0.6,0.85], 'alphaTestRef':0.1,'centerDepthSmooth':0.9975,
        }
        # Shadow rasterization.
        self.bind_fbo([self.shadow_color],self.shadow_depth,2048,2048)
        self.call('glEnable',None,[U],0x0B71); self.call('glDepthMask',None,[C.c_ubyte],1)
        self.call('glClearDepth',None,[C.c_double],1)
        self.call('glClear',None,[U],0x4100)
        self.matrix(0x1701,sp); self.matrix(0x1700,sm@self.translation)
        self.check('shadow setup')
        p=self.use('shadow',folder,opts)
        self.check('shadow uniforms')
        # Never bind the depth attachment as a source while rendering shadow.
        self.uniform(p,'shadowtex0',0)
        self.scene(p,kind)
        self.check('shadow draw')
        # Opaque geometry writes actual normals, materials, masks and HDR color.
        self.bind_fbo([self.buffers[i] for i in range(4)],self.depth)
        self.call('glClearColor',None,[F,F,F,F],0,0,0,0)
        self.call('glClear',None,[U],0x4100)
        self.matrix(0x1701,self.projection); self.matrix(0x1700,self.rotation@self.translation)
        p=self.use('gbuffers_terrain',folder,opts); self.scene(p,kind)
        self.check('terrain draw')
        self.call('glBindTexture',None,[U,U],0x0DE1,self.opaque_depth)
        self.call('glCopyTexSubImage2D',None,[U,I,I,I,I,I,I,I],0x0DE1,0,0,0,0,0,self.w,self.h)
        self.check('depth copy')
        # Deferred + immutable opaque color for refraction/SSR.
        self.call('glDisable',None,[U],0x0B71)
        self.bind_fbo([self.spare[0],self.spare[4]])
        self.use('deferred',folder,opts); self.full_screen()
        self.check('deferred')
        for i in [0,4]:self.buffers[i],self.spare[i]=self.spare[i],self.buffers[i]
        # Transparent water. Already contains transmitted background, output alpha 1.
        if kind not in ['cave','nether','end']:
            self.bind_fbo([self.buffers[0]],self.depth)
            self.call('glEnable',None,[U],0x0B71)
            self.matrix(0x1701,self.projection); self.matrix(0x1700,self.rotation@self.translation)
            p=self.use('gbuffers_water',folder,opts)
            self.quad(p,[(-10,63.8,7),(1,63.8,7),(1,63.8,-5),(-10,63.8,-5)],(0,1,0),(0.28,0.55,0.67),10000)
            self.check('water')
        self.call('glDisable',None,[U],0x0B71)
        stages=[('composite',[0]),('composite1',[5]),('composite2',[6]),('composite3',[5]),('composite4',[0])]
        stage_metrics={}
        for name,outputs in stages:
            small=outputs[0] in [5,6]
            self.bind_fbo([self.spare[i] for i in outputs],w=self.w//4 if small else self.w,h=self.h//4 if small else self.h)
            self.use(name,folder,opts); self.full_screen()
            self.check(name)
            for i in outputs:self.buffers[i],self.spare[i]=self.spare[i],self.buffers[i]
            data=self.read(self.w//4 if small else self.w,self.h//4 if small else self.h)
            assert np.isfinite(data).all(),f'Nonfinite {kind}/{name}'
            stage_metrics[name]={'min':float(data[:,:,:3].min()),'max':float(data[:,:,:3].max())}
        self.bind_fbo([self.final]); self.use('final',folder,opts); self.full_screen()
        pixels=self.read(self.w,self.h)
        error=self.call('glGetError',U,[])
        assert error==0,f'OpenGL error {error:x}'
        assert np.isfinite(pixels).all(),kind
        rgb=pixels[:,:,:3]
        assert rgb.min()>=0 and rgb.max()<=1.001,kind
        assert rgb.std()>0.015 and rgb.mean()>0.005,('Blank output',kind)
        image=Image.fromarray(np.uint8(np.clip(rgb[::-1],0,1)*255))
        return image,{'mean':float(rgb.mean()),'std':float(rgb.std()),'stages':stage_metrics}

    def read(self,w,h):
        data=np.zeros((h,w,4),np.float32)
        self.call('glReadBuffer',None,[U],0x8CE0)
        self.call('glReadPixels',None,[I,I,I,I,U,U,P],0,0,w,h,0x1908,0x1406,data.ctypes.data)
        return data

    def close(self):
        for p in self.programs.values():self.gl.delete_program(p)
        textures=(U*len(self.textures))(*self.textures)
        self.call('glDeleteTextures',None,[I,C.POINTER(U)],len(textures),textures)
        self.call('glDeleteFramebuffers',None,[I,C.POINTER(U)],1,C.byref(self.fbo))
        self.gl.close()

def main():
    renderer=Renderer(); output=ROOT/'validation'; output.mkdir(exist_ok=True)
    report={'type':'Synthetic scene; not Minecraft gameplay','gpu':renderer.gl.info,'scenarios':{}}
    report['shader_sha256']=shader_digest()
    images=[]
    try:
        for kind in ['day','sunset','night','rain','thunder','underwater','cave','nether','end']:
            im,metrics=renderer.render(kind)
            im.save(output/f'{kind}.png'); images.append((kind,im)); report['scenarios'][kind]=metrics
            print(f'{kind}: mean={metrics["mean"]:.4f}, std={metrics["std"]:.4f}',flush=True)
        for profile in PROFILES:
            _,metrics=renderer.render('day',profile)
            report['scenarios'][f'profile_{profile}']=metrics
        _,metrics=renderer.render('day',options={'PBR_MODE':2,'MOTION_BLUR':3,'DOF_QUALITY':3})
        report['scenarios']['pbr_camera_effects']=metrics
        first,_=renderer.render('day',time=42.0); second,_=renderer.render('day',time=42.0)
        assert np.array_equal(np.asarray(first),np.asarray(second)),'Uninitialized frame state'
        report['identical_state_replay']='bit-identical 8-bit output'
        # A static camera with motion blur enabled must not change the image.
        still,_=renderer.render('day',options={'MOTION_BLUR':0}); blur,_=renderer.render('day',options={'MOTION_BLUR':3})
        delta=int(np.abs(np.asarray(still,dtype=int)-np.asarray(blur,dtype=int)).max())
        assert delta<=1,f'Static-camera motion blur: {delta}'
        report['static_camera_motion_blur_max_8bit_difference']=delta
    finally:renderer.close()
    sheet=Image.new('RGB',(640*3,394*3),(16,20,24)); draw=ImageDraw.Draw(sheet)
    for i,(label,im) in enumerate(images):
        x=(i%3)*640; y=(i//3)*394
        sheet.paste(im,(x,y+34)); draw.text((x+14,y+9),'SYNTHETIC GPU FIXTURE / '+label.upper(),fill=(220,228,232))
    sheet.save(output/'contact-sheet.png')
    (output/'render-report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print('Render smoke checks passed.',flush=True)

if __name__=='__main__':main()
