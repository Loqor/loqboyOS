import sys
from array import array

import pygame
import moderngl

pygame.init()

screen = pygame.display.set_mode((800, 480), pygame.OPENGL | pygame.DOUBLEBUF)
display = pygame.Surface((800, 480))
pygame.display.set_caption("PipOS")
pygame.display.set_icon(display)
ctx = moderngl.create_context()

clock = pygame.time.Clock()

img = pygame.image.load('assets/clean.png').convert_alpha()

quad_buffer = ctx.buffer(data=array('f', [
    # position (x, y), uv co-ords (x, y)
    -1.0, 1.0, 0.0, 0.0,  # top left
    1.0, 1.0, 1.0, 0.0,  # top right
    -1.0, -1.0, 0.0, 1.0,  # bottom left
    1.0, -1.0, 1.0, 1.0,  # bottom right
]))

vert_shader = '''
#version 430

in vec4 Position;

uniform mat4 ProjMat;
uniform vec2 InSize;
uniform vec2 OutSize;

out vec2 texCoord;
out vec2 oneTexel;

void main() {
    vec4 outPos = ProjMat * vec4(Position.xy, 0.0, 1.0);
    gl_Position = vec4(outPos.xy, 0.2, 1.0);

    oneTexel = 1.0 / InSize;

    texCoord = Position.xy / OutSize;
}
'''

frag_shader = '''
#version 430

uniform sampler2D DiffuseSampler;
uniform vec2 InSize;
uniform float time;
uniform vec3 colorization;
uniform float brightness;

in vec2 texCoord;
out vec4 fragColor;

const vec4 Zero = vec4(0.0);
const vec4 Half = vec4(0.5);
const vec4 One = vec4(1.0);
const vec4 Two = vec4(2.0);

const float Pi = 3.1415926535;
const float PincushionAmount = 0.02;
const float CurvatureAmount = 0.02;
const float ScanlineAmount = 0.8;
const float ScanlineScale = 480;
const float ScanlineHeight = 1.0;
const float ScanlineBrightScale = 1.0;
const float ScanlineBrightOffset = 0.0;
const float ScanlineOffset = 0.0;
const vec3 Floor = vec3(0.05, 0.05, 0.05);
const vec3 Power = vec3(0.8, 0.8, 0.8);

void main() {
    vec2 PinUnitCoord = texCoord * Two.xy - One.xy;
    float PincushionR2 = pow(length(PinUnitCoord), 2.0);
    vec2 CurvatureClipCurve = PinUnitCoord * CurvatureAmount * PincushionR2;
    vec2 ScreenClipCoord = texCoord;
    ScreenClipCoord -= Half.xy;
    ScreenClipCoord *= One.xy - CurvatureAmount * 0.2;
    ScreenClipCoord += Half.xy;
    ScreenClipCoord += CurvatureClipCurve;

    if (ScreenClipCoord.x < 0.0) discard;
    if (ScreenClipCoord.y < 0.0) discard;
    if (ScreenClipCoord.x > 1.0) discard;
    if (ScreenClipCoord.y > 1.0) discard;

    vec4 InTexel = texture(DiffuseSampler, ScreenClipCoord);

    float InnerSine = texCoord.y * InSize.y * ScanlineScale * 0.25;
    float ScanBrightMod = sin(InnerSine * Pi + (time * 0.12) * InSize.y * 0.25);
    float ScanBrightness = mix(brightness, (pow(ScanBrightMod * ScanBrightMod, ScanlineHeight) * ScanlineBrightScale + 1.0) * 0.5, ScanlineAmount);
    vec3 ScanlineTexel = InTexel.rgb * ScanBrightness;

    vec3 grayscale = vec3(dot(ScanlineTexel, vec3(1, 1, 1)));  // Adjusted grayscale conversion
    grayscale = pow(grayscale, Power);  // Gamma correction

    fragColor = vec4(colorization * grayscale, 1.0);
}
'''


program = ctx.program(vertex_shader=vert_shader, fragment_shader=frag_shader)
render_object = ctx.vertex_array(program, [(quad_buffer, '4f', 'Position')])


def surf_to_texture(surf):
    tex = ctx.texture(surf.get_size(), 4)
    tex.filter = (moderngl.BLEND, moderngl.BLEND)
    tex.swizzle = 'BGRA'
    tex.write(surf.get_view('1'))
    return tex


t = 0

while True:

    display.fill((0, 0, 0))
    img2 = pygame.transform.scale(img, (800, 480))
    display.blit(img2, (0, 0))

    t += 1

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

    frame_tex = surf_to_texture(display)
    frame_tex.use(0)
    program['ProjMat'] = [2.0, 0.0, 0.0, 0.0,
                          0.0, 2.0, 0.0, 0.0,
                          0.0, 0.0, 2.0, 0.0,
                          -1.0, 1.0, 0.0, 2.0]
    program['DiffuseSampler'] = 0
    program['InSize'] = (1, 1)
    program['OutSize'] = (1, -1)
    program['time'] = t
    program['colorization'] = (
        255.0 / 255.0,  # Red
        191.0 / 255.0,  # Green
        0.0 / 255.0     # Blue
    )
    program['brightness'] = 1.0  # Brightness value - default value is 1.0
    render_object.render(mode=moderngl.TRIANGLE_STRIP)

    pygame.display.flip()
    frame_tex.release()
    clock.tick(60)
