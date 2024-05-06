import moderngl_window as mglw
from moderngl_window import geometry as geo
import pygame, sys

pygame.init()

Clock = pygame.time.Clock()
pygame.display.set_mode((1000, 1000))
img = pygame.image.load("assets/Play Rect.png").convert_alpha()

class App(mglw.WindowConfig):
    window_size = 1000, 1000
    resource_dir = 'programs'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # create screen aligned quad
        self.quad = geo.quad_fs()
        self.prog = self.load_program(vertex_shader='vertex_shader.glsl', fragment_shader='fragment_shader.glsl')
        self.set_uniform('resolution', self.window_size)

    def mouse_position_event(self, x: int, y: int, dx: int, dy: int):
        mouse = x, y
        self.set_uniform('mouse', mouse)

    def render(self, time, frame_time):
        self.ctx.clear()
        self.set_uniform('time', time)
        self.quad.render(self.prog)

    def set_uniform(self, uniform, value):
        try:
            self.prog[uniform] = value
        except KeyError:
            print(f'uniform: ' + uniform + ' - not used in shader')


mglw.run_window_config(App)

while 1:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            sys.exit()

    img.blit(img, img.get_rect())
    pygame.display.flip()
    Clock.tick(144)

pygame.quit()