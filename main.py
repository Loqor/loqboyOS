
import sys
import pygame
import moderngl
import spritesheet
from array import array

pygame.init()

# When we do the actual Pip Boy, I'm pretty sure we can just get the window's scale instead
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 480

widthX = SCREEN_WIDTH / 2
heightY = SCREEN_HEIGHT / 2

# These are horrible, no good, very bad
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

# Flicker start up, self-evident by the name. make this 'False' if you don't want it to appear on startup
startUpFlicker = False

# ModernGL context, it's for the actual rendering
ctx = moderngl.create_context()

# Clock value, dictates the speed of the game
clock = pygame.time.Clock()

# Indexes for different tabs/submenus in the Pip Boy
indexOfTab = 0
indexOfSubmenu = 0

# Sprite sheet stuff for the Vault Boy
sprite_sheet_image = pygame.image.load('assets/vault_boy/vault_boy_sequence.png').convert_alpha()
sprite_sheet = spritesheet.SpriteSheet(sprite_sheet_image)

# Frames for Vault Boy
animation_list = []
animation_steps = 6
last_update = pygame.time.get_ticks()
animation_cooldown = 250
frame = 0

# For loop iterating through the animations
for x in range(animation_steps):
    animation_list.append(sprite_sheet.get_image(x, 268, 268, 1, (0, 0, 0)))

# For the submenus. @TODO I REFUSE TO ORGANIZE I'LL DO IT LATER
defaultStatusPos = (100, 40)
defaultSpecialPos = (196, 40)
defaultPerksPos = (300, 40)
statusPos = defaultStatusPos
specialPos = defaultSpecialPos
perksPos = defaultPerksPos

font = pygame.font.Font('fonts/monofonto rg.ttf', 26)
font_smaller = pygame.font.Font('fonts/monofonto rg.ttf', 24)
font_scaled = pygame.font.Font('fonts/monofonto rg.ttf', 22)
font_for_bars = pygame.font.Font('fonts/monofonto rg.ttf', 18)
font2 = pygame.font.Font('fonts/RobotoCondensed-Regular.ttf', 26)

background = pygame.image.load('assets/base.png').convert_alpha()

quad_buffer = ctx.buffer(data=array('f', [
    # position (x, y), uv co-ords (x, y)
    -1.0, 1.0, 0.0, 0.0,  # top left
    1.0, 1.0, 1.0, 0.0,  # top right
    -1.0, -1.0, 0.0, 1.0,  # bottom left
    1.0, -1.0, 1.0, 1.0,  # bottom right
]))

vert_shader = open('shaders/vertex_shader.glsl').read()

frag_shader = open('shaders/fragment_shader.glsl').read()

program = ctx.program(vertex_shader=vert_shader, fragment_shader=frag_shader)
render_object = ctx.vertex_array(program, [(quad_buffer, '4f', 'Position')])


def surf_to_texture(surf):
    tex = ctx.texture(surf.get_size(), 4)
    tex.filter = (moderngl.BLEND, moderngl.BLEND)
    tex.swizzle = 'BGRA'
    tex.write(surf.get_view('1'))
    return tex


# BUTTONS
STATButton = pygame.Surface((100, 26), pygame.SRCALPHA).convert_alpha()
INVButton = pygame.Surface((100, 26), pygame.SRCALPHA).convert_alpha()
DATAButton = pygame.Surface((100, 26), pygame.SRCALPHA).convert_alpha()
MAPButton = pygame.Surface((100, 26), pygame.SRCALPHA).convert_alpha()
RADIOButton = pygame.Surface((100, 26), pygame.SRCALPHA).convert_alpha()
NameLabel = pygame.Surface((800, 26), pygame.SRCALPHA).convert_alpha()

# Stats Screen Specific Buttons
STATUSButton = pygame.Surface((100, 24), pygame.SRCALPHA).convert_alpha()
SPECIALButton = pygame.Surface((100, 24), pygame.SRCALPHA).convert_alpha()
PERKSButton = pygame.Surface((60, 24), pygame.SRCALPHA).convert_alpha()

# Stats Screen Specific Rectangles
STATUSButtonRect = pygame.Rect(statusPos[0], statusPos[1], 100, 50)  # 110 40 100 50
SPECIALButtonRect = pygame.Rect(specialPos[0], specialPos[1], 100, 50)  # 192 40 100 50
PERKSButtonRect = pygame.Rect(perksPos[0], perksPos[1], 100, 50)  # 286 40 100 50

STATButtonRect = pygame.Rect(97, heightY - 234, 100, 26)
INVButtonRect = pygame.Rect(219, heightY - 234, 100, 26)
DATAButtonRect = pygame.Rect(widthX - 62, heightY - 234, 100, 26)
MAPButtonRect = pygame.Rect(widthX + 67, heightY - 234, 100, 26)
RADIOButtonRect = pygame.Rect(widthX + 223, heightY - 234, 100, 26)
LabelOfName = pygame.Rect((display.get_width() / 2) - (NameLabel.get_width() / 2), display.get_height() / 2 + 150, 286,
                          26)

t = 0
statColor = (120, 120, 120)
invColor = (120, 120, 120)
dataColor = (120, 120, 120)
mapColor = (120, 120, 120)
radioColor = (120, 120, 120)

selectedColor = (174, 174, 174)

statusColor = (91, 91, 91)
specialColor = (50, 50, 50)
perksColor = (10, 10, 10)


lerp_speed = t * 0.2  # Higher values make the transition faster

def lerp(a, b, t):
    return a + (b - a) * t

def translate_submenu_rects(index):
    global STATUSButtonRect, SPECIALButtonRect, PERKSButtonRect

    if index == 0:
        # Transition to Stats
        STATUSButtonRect.x = lerp(STATUSButtonRect.x, defaultStatusPos[0], lerp_speed)
        SPECIALButtonRect.x = lerp(SPECIALButtonRect.x, defaultSpecialPos[0], lerp_speed)
        PERKSButtonRect.x = lerp(PERKSButtonRect.x, defaultPerksPos[0], lerp_speed)

    elif index == 1:
        # Transition to Special
        STATUSButtonRect.x = lerp(STATUSButtonRect.x, defaultStatusPos[0] - (defaultSpecialPos[0] - defaultStatusPos[0]), lerp_speed)
        SPECIALButtonRect.x = lerp(SPECIALButtonRect.x, defaultSpecialPos[0], lerp_speed)
        PERKSButtonRect.x = lerp(PERKSButtonRect.x, defaultPerksPos[0] + (defaultStatusPos[0] - defaultSpecialPos[0]), lerp_speed)

    elif index == 2:
        # Transition to Perks
        STATUSButtonRect.x = lerp(STATUSButtonRect.x, defaultStatusPos[0] - (defaultPerksPos[0] - defaultStatusPos[0]), lerp_speed)
        SPECIALButtonRect.x = lerp(SPECIALButtonRect.x, defaultSpecialPos[0] - (defaultPerksPos[0] - defaultSpecialPos[0]), lerp_speed)
        PERKSButtonRect.x = lerp(PERKSButtonRect.x, defaultPerksPos[0], lerp_speed)



while True:

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        if event.type == pygame.MOUSEBUTTONDOWN and not startUpFlicker and event.button == 1:
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
            if STATUSButtonRect.collidepoint(pygame.mouse.get_pos()):
                indexOfSubmenu = 0
                translate_submenu_rects(indexOfSubmenu)
                statusColor = (91, 91, 91)
                specialColor = (50, 50, 50)
                perksColor = (10, 10, 10)
            if SPECIALButtonRect.collidepoint(pygame.mouse.get_pos()):
                indexOfSubmenu = 1
                translate_submenu_rects(indexOfSubmenu)
                statusColor = (50, 50, 50)
                specialColor = (91, 91, 91)
                perksColor = (50, 50, 50)
            if PERKSButtonRect.collidepoint(pygame.mouse.get_pos()):
                indexOfSubmenu = 2
                translate_submenu_rects(indexOfSubmenu)
                statusColor = (10, 10, 10)
                specialColor = (50, 50, 50)
                perksColor = (91, 91, 91)
        if STATButtonRect.collidepoint(pygame.mouse.get_pos()):
            statColor = (174, 174, 174)
        else:
            statColor = (91, 91, 91)
        if INVButtonRect.collidepoint(pygame.mouse.get_pos()):
            invColor = (174, 174, 174)
        else:
            invColor = (91, 91, 91)
        if DATAButtonRect.collidepoint(pygame.mouse.get_pos()):
            dataColor = (174, 174, 174)
        else:
            dataColor = (91, 91, 91)
        if MAPButtonRect.collidepoint(pygame.mouse.get_pos()):
            mapColor = (174, 174, 174)
        else:
            mapColor = (91, 91, 91)
        if RADIOButtonRect.collidepoint(pygame.mouse.get_pos()):
            radioColor = (174, 174, 174)
        else:
            radioColor = (91, 91, 91)
        if STATUSButtonRect.collidepoint(pygame.mouse.get_pos()):
            statusColor = selectedColor
        else:
            statusColor = (91, 91, 91)
        if SPECIALButtonRect.collidepoint(pygame.mouse.get_pos()):
            specialColor = selectedColor
        else:
            specialColor = (50, 50, 50)
        if PERKSButtonRect.collidepoint(pygame.mouse.get_pos()):
            perksColor = selectedColor
        else:
            perksColor = (10, 10, 10)

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

    # Submenus for Stats
    status = font_smaller.render("STATUS", True, statusColor)
    status_rect = status.get_rect(center=(STATUSButton.get_width() / 2, STATUSButton.get_height() / 2))
    special = font_smaller.render("SPECIAL", True, specialColor)
    special_rect = special.get_rect(center=(SPECIALButton.get_width() / 2, SPECIALButton.get_height() / 2))
    perks = font_smaller.render("PERKS", True, perksColor)
    perks_rect = perks.get_rect(center=(PERKSButton.get_width() / 2, PERKSButton.get_height() / 2))

    # Name
    name = font2.render("Reanu Keeves", True, (174, 174, 174))
    rectOfName = name.get_rect(center=(NameLabel.get_width() / 2, NameLabel.get_height() / 2))

    STATButton.blit(stats, statsRect)
    INVButton.blit(inv, invRect)
    DATAButton.blit(data, dataRect)
    MAPButton.blit(maps, mapRect)
    RADIOButton.blit(radio, radioRect)
    NameLabel.blit(name, rectOfName)

    # Rendering code, ANIME DO NOT TOUCH OR I WILL SMITE YOU WITH A FUCKING NUCLEAR BOMB
    t += 1


    def get_tab_representation(index, tablist):
        for item in tablist:
            if item[0] == index:
                return item[1]
        return None  # Return None if no matching index is found


    display.fill((0, 0, 0))

    # Display each button
    display.blit(STATButton, (STATButtonRect.x, STATButtonRect.y))
    display.blit(INVButton, (INVButtonRect.x, INVButtonRect.y))
    display.blit(DATAButton, (DATAButtonRect.x, DATAButtonRect.y))
    display.blit(MAPButton, (MAPButtonRect.x, MAPButtonRect.y))
    display.blit(RADIOButton, (RADIOButtonRect.x, RADIOButtonRect.y))

    # Display tab selections
    display.blit(font.render(get_tab_representation(indexOfTab, selectedTabTop), True, (91, 91, 91)), (24, 0))
    display.blit(font.render(get_tab_representation(indexOfTab, selectedTabBtm), True, (91, 91, 91)), (24, 24))

    if indexOfTab == 0:

        # Display different submenus
        STATUSButton.blit(status, status_rect)
        SPECIALButton.blit(special, special_rect)
        PERKSButton.blit(perks, perks_rect)

        # display stats buttons
        display.blit(STATUSButton, (STATUSButtonRect.x, STATUSButtonRect.y))
        display.blit(SPECIALButton, (SPECIALButtonRect.x, SPECIALButtonRect.y))
        display.blit(PERKSButton, (PERKSButtonRect.x, PERKSButtonRect.y))

        # Display lower bar of Stats screen
        display.blit(font.render("██████████▌██████████████████████████████████▌███████████", True, (50, 50, 50)),
                     (34, heightY + 200))
        display.blit(
            font_scaled.render("                        ▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀          ", True, (174, 174, 174)),
            (34, heightY + 209))
        display.blit(font_scaled.render("HP 380/380    LEVEL 125                                  AP 150/150", True,
                                        (174, 174, 174)), (34, heightY + 202))
        # Display Limb Health Bars

        if indexOfSubmenu == 0:

            # Update animation
            current_time = pygame.time.get_ticks()
            if current_time - last_update >= animation_cooldown:
                frame += 1
                last_update = current_time
                if frame >= len(animation_list):
                    frame = 0

            # Vault boy rendering
            display.blit(animation_list[frame], (widthX - 168, heightY - 162))

            # Display name
            display.blit(NameLabel, (LabelOfName.x, LabelOfName.y))

            bar = "▀▀▀▀▀"

            for i in range(6):
                values = [
                    (400 - 24, heightY - 152),
                    (400 - 134, heightY - 70),
                    (400 + 84, heightY - 70),
                    (400 - 134, heightY + 64),
                    (400 + 84, heightY + 64),
                    (400 - 24, heightY + 98),
                ]
                display.blit(font_for_bars.render(bar, True, (174, 174, 174)), values[i])

        if indexOfSubmenu == 1:

        # special screen
            display.blit(font.render("██████████████████████████", True, (91, 91, 91)), (53, heightY - 120))
            display.blit(font.render(" Strength               2", True, (0, 0, 0)), (53, heightY - 120))
            display.blit(font.render(" Perception             5", True, (91, 91, 91)), (53, heightY - 80))
            display.blit(font.render(" Endurance              5", True, (91, 91, 91)), (53, heightY - 40))
            display.blit(font.render(" Charisma              10", True, (91, 91, 91)), (53, heightY - 0))
            display.blit(font.render(" Intelligence          10", True, (91, 91, 91)), (53, heightY + 40))
            display.blit(font.render(" Agility                6", True, (91, 91, 91)), (53, heightY + 80))
            display.blit(font.render(" Luck                  15", True, (91, 91, 91)), (53, heightY + 120))



        if indexOfSubmenu == 2:
            # perks screen
            display.blit(font.render("████████████████████████████", True, (91, 91, 91)), (53, heightY - 120))
            display.blit(font.render(" This perk is temporary lol", True, (0, 0, 0)), (53, heightY - 120))
            display.blit(font.render(" This perk is temporary lol", True, (91, 91, 91)), (53, heightY - 80))
            display.blit(font.render(" This perk is temporary lol", True, (91, 91, 91)), (53, heightY - 40))
    frame_tex = surf_to_texture(display)
    frame_tex.use(0)

    # Program Uniforms (for shaders, **do not touch**).
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
    if startUpFlicker:
        brightness = ((t * 0.002) / 0.28)
    else:
        brightness = 1  # Brightness value - default value is 1.0
    program['brightness'] = brightness
    program['shuckScreen'] = startUpFlicker
    timeRunning = 0.0
    if startUpFlicker:
        timeRunning = t * 0.002
        print(timeRunning)
        if timeRunning >= 0.28:
            startUpFlicker = False
            timeRunning = 0
    else:
        timeRunning = 0
    program['timeRunning'] = timeRunning

    # Actual rendering of the screen itself
    ctx.clear(0, 0, 0, 1, -1)
    render_object.render(mode=moderngl.TRIANGLE_STRIP)

    # Frame update
    pygame.display.flip()
    frame_tex.release()
    clock.tick(75)
