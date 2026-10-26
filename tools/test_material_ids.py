"""GPU regression: categorical material IDs must survive perspective rasterization."""
import unittest
import numpy as np
from build import SHADERS
from validate import source_for
from render_smoke import Renderer, U, F, perspective


class MaterialIdRegression(unittest.TestCase):
    def test_perspective_material_boundaries(self):
        r = Renderer(192, 128)
        vertex = source_for(SHADERS / 'gbuffers_terrain.vsh')
        fragment = '''#version 330 compatibility
flat in float vId;
uniform float expectedId;
void main() {
    if (vId == 0.0) discard;
    gl_FragColor = vec4(float(vId == expectedId),
        float(vId >= 10101.0 && vId <= 10106.0), 0.0, 1.0);
}'''
        p = r.gl.compile(vertex, fragment)
        results = []
        try:
            r.bind_fbo([r.final])
            r.call('glUseProgram', None, [U], p)
            identity = np.eye(4, dtype=np.float32)
            r.matrix(0x1700, identity)
            r.matrix(0x1701, perspective(1.5))
            for name in ['gbufferModelView', 'gbufferModelViewInverse']:
                r.uniform(p, name, identity)
            # A receding tilted quad, plus subpixel camera motion: this exposes
            # rounding at the first/last IDs rather than just a front-on square.
            for material in [10101, 10102, 10106, 10000, 10004, 10110, 10115, 10117]:
                r.uniform(p, 'expectedId', float(material))
                for shift in [0.0, 0.003, 0.017]:
                    r.call('glClearColor', None, [F]*4, 0, 0, 0, 0)
                    r.call('glClear', None, [U], 0x4000)
                    r.quad(p, [(-0.4+shift,-0.4,-0.8), (1.8+shift,-1.8,-4.0),
                               (1.8+shift,1.8,-4.0), (-0.4+shift,0.4,-0.8)],
                           (0,0,1), (1,1,1), block=material)
                    data = r.read(192,128)
                    mask = data[:,:,3] > 0.5
                    self.assertGreater(int(mask.sum()), 1000)
                    self.assertTrue(np.all(data[:,:,0][mask] == 1.0), material)
                    self.assertTrue(np.all(data[:,:,1][mask] == float(10101 <= material <= 10106)), material)
                    results.append(int(mask.sum()))
            r.check('flat material boundary regression')
        finally:
            r.gl.delete_program(p)
            r.close()
        print(f'Checked {len(results)} material/camera cases; every covered pixel retained its exact ID.')


if __name__ == '__main__':
    unittest.main()
