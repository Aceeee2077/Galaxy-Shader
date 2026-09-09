"""Small hidden WGL context for real driver compilation and offscreen verification.

No desktop input, game automation, network access or third-party runtime required.
"""
import ctypes as C
from ctypes import wintypes as W

class PixelFormat(C.Structure):
    _fields_=[('nSize',W.WORD),('nVersion',W.WORD),('dwFlags',W.DWORD),
              ('iPixelType',W.BYTE),('cColorBits',W.BYTE),('cRedBits',W.BYTE),
              ('cRedShift',W.BYTE),('cGreenBits',W.BYTE),('cGreenShift',W.BYTE),
              ('cBlueBits',W.BYTE),('cBlueShift',W.BYTE),('cAlphaBits',W.BYTE),
              ('cAlphaShift',W.BYTE),('cAccumBits',W.BYTE),('cAccumRedBits',W.BYTE),
              ('cAccumGreenBits',W.BYTE),('cAccumBlueBits',W.BYTE),('cAccumAlphaBits',W.BYTE),
              ('cDepthBits',W.BYTE),('cStencilBits',W.BYTE),('cAuxBuffers',W.BYTE),
              ('iLayerType',W.BYTE),('bReserved',W.BYTE),('dwLayerMask',W.DWORD),
              ('dwVisibleMask',W.DWORD),('dwDamageMask',W.DWORD)]

class GLContext:
    def __init__(self):
        self.user=C.WinDLL('user32',use_last_error=True)
        self.gdi=C.WinDLL('gdi32',use_last_error=True)
        self.dll=C.WinDLL('opengl32',use_last_error=True)
        self.user.CreateWindowExW.argtypes=[W.DWORD,W.LPCWSTR,W.LPCWSTR,W.DWORD,C.c_int,C.c_int,C.c_int,C.c_int,W.HWND,W.HMENU,W.HINSTANCE,C.c_void_p]
        self.user.CreateWindowExW.restype=W.HWND
        self.user.GetDC.argtypes=[W.HWND]; self.user.GetDC.restype=W.HDC
        self.user.ReleaseDC.argtypes=[W.HWND,W.HDC]
        self.user.DestroyWindow.argtypes=[W.HWND]
        self.gdi.ChoosePixelFormat.argtypes=[W.HDC,C.POINTER(PixelFormat)]
        self.gdi.SetPixelFormat.argtypes=[W.HDC,C.c_int,C.POINTER(PixelFormat)]
        self.dll.wglCreateContext.argtypes=[W.HDC]; self.dll.wglCreateContext.restype=C.c_void_p
        self.dll.wglMakeCurrent.argtypes=[W.HDC,C.c_void_p]
        self.dll.wglDeleteContext.argtypes=[C.c_void_p]
        self.dll.wglGetProcAddress.argtypes=[C.c_char_p]; self.dll.wglGetProcAddress.restype=C.c_void_p
        # Built-in STATIC class, no WS_VISIBLE flag: only an offscreen drawable.
        self.window=self.user.CreateWindowExW(0,'STATIC','Galaxy Shader GPU validation',0,0,0,32,32,None,None,None,None)
        if not self.window: raise OSError(C.get_last_error(),'Cannot create hidden GL window')
        self.dc=self.user.GetDC(self.window)
        pfd=PixelFormat(); pfd.nSize=C.sizeof(pfd); pfd.nVersion=1
        pfd.dwFlags=0x24; pfd.cColorBits=32; pfd.cDepthBits=24
        pixel=self.gdi.ChoosePixelFormat(self.dc,C.byref(pfd))
        if not pixel or not self.gdi.SetPixelFormat(self.dc,pixel,C.byref(pfd)):
            raise RuntimeError('Cannot select hardware pixel format')
        self.context=self.dll.wglCreateContext(self.dc)
        if not self.context or not self.dll.wglMakeCurrent(self.dc,self.context):
            raise RuntimeError('Cannot create current OpenGL context')
        self.functions={}
        get=self.fn('glGetString',C.c_char_p,C.c_uint)
        self.info={key:get(enum).decode() for key,enum in [('vendor',0x1F00),('renderer',0x1F01),('version',0x1F02),('glsl',0x8B8C)]}

    def fn(self,name,result,*args):
        if name not in self.functions:
            address=self.dll.wglGetProcAddress(name.encode())
            if address and address not in (1,2,3,0xffffffffffffffff):
                function=C.WINFUNCTYPE(result,*args)(address)
            else:
                function=getattr(self.dll,name)
                function.restype=result; function.argtypes=list(args)
            self.functions[name]=function
        return self.functions[name]

    def compile(self,vert,frag):
        shaders=[]
        for kind,source in [(0x8B31,vert),(0x8B30,frag)]:
            sh=self.fn('glCreateShader',C.c_uint,C.c_uint)(kind)
            text=C.c_char_p(source.encode())
            self.fn('glShaderSource',None,C.c_uint,C.c_int,C.POINTER(C.c_char_p),C.POINTER(C.c_int))(sh,1,C.byref(text),None)
            self.fn('glCompileShader',None,C.c_uint)(sh)
            ok=C.c_int()
            self.fn('glGetShaderiv',None,C.c_uint,C.c_uint,C.POINTER(C.c_int))(sh,0x8B81,C.byref(ok))
            if not ok.value:
                buf=C.create_string_buffer(32768)
                self.fn('glGetShaderInfoLog',None,C.c_uint,C.c_int,C.POINTER(C.c_int),C.c_void_p)(sh,len(buf),None,buf)
                raise RuntimeError(('VERTEX' if kind==0x8B31 else 'FRAGMENT')+'\n'+buf.value.decode())
            shaders.append(sh)
        program=self.fn('glCreateProgram',C.c_uint)()
        for sh in shaders: self.fn('glAttachShader',None,C.c_uint,C.c_uint)(program,sh)
        for name,index in [('mc_Entity',10),('mc_midTexCoord',11),('at_tangent',12)]:
            self.fn('glBindAttribLocation',None,C.c_uint,C.c_uint,C.c_char_p)(program,index,name.encode())
        self.fn('glLinkProgram',None,C.c_uint)(program)
        ok=C.c_int()
        self.fn('glGetProgramiv',None,C.c_uint,C.c_uint,C.POINTER(C.c_int))(program,0x8B82,C.byref(ok))
        for sh in shaders: self.fn('glDeleteShader',None,C.c_uint)(sh)
        if not ok.value:
            buf=C.create_string_buffer(32768)
            self.fn('glGetProgramInfoLog',None,C.c_uint,C.c_int,C.POINTER(C.c_int),C.c_void_p)(program,len(buf),None,buf)
            raise RuntimeError('LINK\n'+buf.value.decode())
        return program

    def delete_program(self,program):
        self.fn('glDeleteProgram',None,C.c_uint)(program)

    def close(self):
        self.dll.wglMakeCurrent(None,None)
        self.dll.wglDeleteContext(self.context)
        self.user.ReleaseDC(self.window,self.dc)
        self.user.DestroyWindow(self.window)
