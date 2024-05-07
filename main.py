import sys
from array import array

import pygame
import moderngl

import imageio.v2 as imageio

pygame.init()

SCREEN_WIDTH = 800
SCREEN_HEIGHT = 480
widthX = SCREEN_WIDTH / 2
heightY = SCREEN_HEIGHT / 2
selectedTabTop = [
    [0, "      ┌     ┐                                             "],
    [1, "                ┌    ┐                                    "],
    [2, "                         ┌    ┐                           "],
    [3, "                                   ┌    ┐                 "],
    [4, "                                              ┌      ┐    "],
]
selectedTabBtm = [
    [0, "┌─────┘     └────────────────────────────────────────────┐"],
    [1, "┌───────────────┘    └───────────────────────────────────┐"],
    [2, "┌────────────────────────┘    └──────────────────────────┐"],
    [3, "┌──────────────────────────────────┘    └────────────────┐"],
    [4, "┌─────────────────────────────────────────────┘      └───┐"],
]

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.OPENGL | pygame.DOUBLEBUF)
display = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("PipOS")
pygame.display.set_icon(display)
ctx = moderngl.create_context()

clock = pygame.time.Clock()
indexOfTab = 0
shouldBlip = False

font = pygame.font.Font('fonts/monofonto rg.ttf', 26)
font_scaled = pygame.font.Font('fonts/monofonto rg.ttf', 22)
font2 = pygame.font.Font('fonts/RobotoCondensed-Regular.ttf', 26)

background = pygame.image.load('assets/base.png').convert_alpha()

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
uniform bool shuckScreen;
uniform float timeRunning;

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
const float ScanlineScale = 560;
const float ScanlineHeight = 1.0;
const float ScanlineBrightScale = 1.0;
const float ScanlineBrightOffset = 0.0;
const float ScanlineOffset = 0.0;
const vec3 Floor = vec3(0.05, 0.05, 0.05);
const vec3 Power = vec3(0.8, 0.8, 0.8);

void main() {
    vec2 modifiedTexCoord = texCoord;
    float scanlineScaleFactor = 0.0;

    // Check if shuckScreen is greater than 0 and scroll the screen
    if (shuckScreen) {
        float baseSpeed = timeRunning; // Initial speed of the scrolling
        float scrollSpeed = 0;

        scrollSpeed = min(baseSpeed, 0.44);

        modifiedTexCoord.y += time * scrollSpeed;
        
        // Optional: Wrap around the texture coordinate to create a continuous scroll
        modifiedTexCoord.y = fract(modifiedTexCoord.y);

        // Setting ScanlineScale to -20 when shuckScreen is greater than 0
        scanlineScaleFactor = 470;
        
        if(baseSpeed >= 0.44) {
            modifiedTexCoord = texCoord;
        }
    }

    vec2 PinUnitCoord = modifiedTexCoord * Two.xy - One.xy;
    float PincushionR2 = pow(length(PinUnitCoord), 2.0);
    vec2 CurvatureClipCurve = PinUnitCoord * CurvatureAmount * PincushionR2;
    vec2 ScreenClipCoord = modifiedTexCoord;
    ScreenClipCoord -= Half.xy;
    ScreenClipCoord *= One.xy - CurvatureAmount * 0.2;
    ScreenClipCoord += Half.xy;
    ScreenClipCoord += CurvatureClipCurve;

    if (ScreenClipCoord.x < 0.0) discard;
    if (ScreenClipCoord.y < 0.0) discard;
    if (ScreenClipCoord.x > 1.0) discard;
    if (ScreenClipCoord.y > 1.0) discard;

    vec4 InTexel = texture(DiffuseSampler, ScreenClipCoord);

    float InnerSine = modifiedTexCoord.y * InSize.y * (ScanlineScale - scanlineScaleFactor) * 0.25;
    float ScanBrightMod = sin(InnerSine * Pi + (time * 0.12) * InSize.y * 0.25);
    float ScanBrightness = brightness * mix(1.0, (pow(ScanBrightMod * ScanBrightMod, ScanlineHeight) * (ScanlineBrightScale + (scanlineScaleFactor / 1000) + 1.0)) * 0.5, ScanlineAmount);
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


# BUTTONS
STATButton = pygame.Surface((100, 50), pygame.SRCALPHA)
INVButton = pygame.Surface((100, 50), pygame.SRCALPHA)
DATAButton = pygame.Surface((100, 50), pygame.SRCALPHA)
MAPButton = pygame.Surface((100, 50), pygame.SRCALPHA)
RADIOButton = pygame.Surface((100, 50), pygame.SRCALPHA)
NameLabel = pygame.Surface((286, 26), pygame.SRCALPHA)

STATButtonRect = pygame.Rect(97, heightY - 242, 100, 50)
INVButtonRect = pygame.Rect(219, heightY - 242, 100, 50)
DATAButtonRect = pygame.Rect(widthX - 62, heightY - 242, 100, 50)
MAPButtonRect = pygame.Rect(widthX + 67, heightY - 242, 100, 50)
RADIOButtonRect = pygame.Rect(widthX + 223, heightY - 242, 100, 50)
labelname = pygame.Rect((display.get_width() / 2) - (NameLabel.get_width() / 2), display.get_height() / 2 + 150, 286, 26)

t = 0
statColor = (0, 120, 120)
invColor = (0, 120, 120)
dataColor = (0, 120, 120)
mapColor = (0, 120, 120)
radioColor = (0, 120, 120)

while True:

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        if event.type == pygame.MOUSEBUTTONDOWN and not shouldBlip and event.button == 1:
            if STATButtonRect.collidepoint(event.pos):
                indexOfTab = 0
            if INVButtonRect.collidepoint(event.pos):
                indexOfTab = 1
            if DATAButtonRect.collidepoint(event.pos):
                indexOfTab = 2
            if MAPButtonRect.collidepoint(event.pos):
                indexOfTab = 3
            if RADIOButtonRect.collidepoint(event.pos):
                indexOfTab = 4
        if STATButtonRect.collidepoint(pygame.mouse.get_pos()):
            statColor = (0, 255, 255)
        else:
            statColor = (0, 120, 120)
        if INVButtonRect.collidepoint(pygame.mouse.get_pos()):
            invColor = (0, 255, 255)
        else:
            invColor = (0, 120, 120)
        if DATAButtonRect.collidepoint(pygame.mouse.get_pos()):
            dataColor = (0, 255, 255)
        else:
            dataColor = (0, 120, 120)
        if MAPButtonRect.collidepoint(pygame.mouse.get_pos()):
            mapColor = (0, 255, 255)
        else:
            mapColor = (0, 120, 120)
        if RADIOButtonRect.collidepoint(pygame.mouse.get_pos()):
            radioColor = (0, 255, 255)
        else:
            radioColor = (0, 120, 120)

    stats = font.render("STAT", True, statColor)
    statsRect = stats.get_rect(center=(STATButton.get_width() / 2, STATButton.get_height() / 2))
    inv = font.render("INV", True, invColor)
    invRect = inv.get_rect(center=(INVButton.get_width() / 2, INVButton.get_height() / 2))
    data = font.render("DATA", True, dataColor)
    dataRect = data.get_rect(center=(DATAButton.get_width() / 2, DATAButton.get_height() / 2))
    maps = font.render("MAP", True, mapColor)
    mapRect = maps.get_rect(center=(MAPButton.get_width() / 2, MAPButton.get_height() / 2))
    radio = font.render("RADIO", True, radioColor)
    radioRect = radio.get_rect(center=(RADIOButton.get_width() / 2, RADIOButton.get_height() / 2))

    # Name
    name = font2.render("animecheeze", True, (0, 238, 0))
    rectOfName = name.get_rect(center=(NameLabel.get_width() / 2, NameLabel.get_height() / 2))

    STATButton.blit(stats, statsRect)
    INVButton.blit(inv, invRect)
    DATAButton.blit(data, dataRect)
    MAPButton.blit(maps, mapRect)
    RADIOButton.blit(radio, radioRect)
    NameLabel.blit(name, rectOfName)

    # Rendering code, ANIME DO NOT TOUCH OR I WILL SMITE YOU WITH A FUCKING NUCLEAR BOMB
    t += 1


    def get_tab_representation(index, listof):
        for item in listof:
            if item[0] == index:
                return item[1]
        return None  # Return None if no matching index is found

    display.fill((0, 0, 0))
    # background_scaled = pygame.transform.scale(background, (800, 480))
    # display.blit(background_scaled, (0, 0))
    # display.blit(background_scaled, (0, 0))
    # pipman = pygame.image.load("assets/vault_boy_gif.gif").convert_alpha()
    # pipmy = pygame.transform.scale(pipman, (800, 480))
    # display.blit(pipman, (widthX - 242, heightY))

    display.blit(STATButton, (STATButtonRect.x, STATButtonRect.y))
    display.blit(INVButton, (INVButtonRect.x, INVButtonRect.y))
    display.blit(DATAButton, (DATAButtonRect.x, DATAButtonRect.y))
    display.blit(MAPButton, (MAPButtonRect.x, MAPButtonRect.y))
    display.blit(RADIOButton, (RADIOButtonRect.x, RADIOButtonRect.y))
    display.blit(NameLabel, (labelname.x, labelname.y))
    display.blit(font.render(get_tab_representation(indexOfTab, selectedTabTop), True, (0, 238, 0)), (24, 0))
    display.blit(font.render(get_tab_representation(indexOfTab, selectedTabBtm), True, (0, 238, 0)), (24, 24))
    display.blit(       font.render("██████████▌██████████████████████████████████▌███████████", True, (0, 95, 0)), (34,heightY +200))
    display.blit(font_scaled.render("                        ▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀          ", True, (0, 238, 0)), (34,heightY + 209))
    display.blit(font_scaled.render("HP 380/380    LEVEL 125                                  AP 150/150", True, (0, 238, 0)), (34,heightY +202))

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
        0.0 / 255.0,  # Red
        238.0 / 255.0,  # Green
        0.0 / 255.0  # Blue
    )
    brightness = 0
    if shouldBlip:
        brightness = ((t * 0.001) / 0.44)
    else:
        brightness = 1  # Brightness value - default value is 1.0
    program['brightness'] = brightness
    program['shuckScreen'] = shouldBlip
    timeRunning = 0.0
    if shouldBlip:
        timeRunning = t * 0.001
        if timeRunning > 0.44:
            shouldBlip = False
    else:
        timeRunning = 0
    program['timeRunning'] = timeRunning
    render_object.render(mode=moderngl.TRIANGLE_STRIP)

    pygame.display.flip()
    frame_tex.release()
    clock.tick(60)
