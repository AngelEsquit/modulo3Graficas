import pygame
import pygame.display
from pygame.locals import *

from gl import Renderer
from buffer import Buffer
from model import Model
from vertexShaders import *
from fragmentShaders import *

width = 960
height = 540

deltaTime = 0.0


screen = pygame.display.set_mode((width, height), pygame.DOUBLEBUF | pygame.OPENGL)
clock = pygame.time.Clock()


rend = Renderer(screen)

rend.SetShaders(vertex_shader, fragment_shader)

faceModel = Model("models/model.obj")
faceModel.AddTexture("textures/model.bmp")
faceModel.position.z = -5

rend.scene.append(faceModel)

isRunning = True

while isRunning:

	deltaTime = clock.tick(60) / 1000

	keys = pygame.key.get_pressed()

	for event in pygame.event.get():
		if event.type == pygame.QUIT:
			isRunning = False

		elif event.type == pygame.KEYDOWN:
			if event.key == pygame.K_f:
				rend.ToggleFilledMode()


	if keys[K_UP]:
		rend.camera.position.y += 1 * deltaTime

	if keys[K_DOWN]:
		rend.camera.position.y -= 1 * deltaTime

	if keys[K_RIGHT]:
		rend.camera.position.x += 1 * deltaTime

	if keys[K_LEFT]:
		rend.camera.position.x -= 1 * deltaTime

	if keys[K_w]:
		rend.camera.position.z += 1 * deltaTime

	if keys[K_s]:
		rend.camera.position.z -= 1 * deltaTime

	faceModel.rotation.y += 45 * deltaTime


	rend.Render()
	pygame.display.flip()

pygame.quit()