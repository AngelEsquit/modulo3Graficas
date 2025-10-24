import pygame
import pygame.display
from pygame.locals import *

import glm

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
rend.pointLight = glm.vec3(1,1,1)

# Default to new custom shaders
currVertexShader = twist_vertex_shader
currFragmentShader = fresnel_fragment_shader

rend.SetShaders(currVertexShader, currFragmentShader)

skyboxTextures = ["skybox/right.jpg",
				  "skybox/left.jpg",
				  "skybox/top.jpg",
				  "skybox/bottom.jpg",
				  "skybox/front.jpg",
				  "skybox/back.jpg"]

rend.CreateSkybox(skyboxTextures)


# Load Bucket Axolotl model with its texture
axolotl = Model("models/BucketAxolotl/Bucket_axolotl.obj")
axolotl.AddTexture("textures/BucketAxolotl/lucy.png")
# Optional: add second texture if you want to try multi-texture shaders
# axolotl.AddTexture("textures/BucketAxolotl/internal_ground_ao_texture.jpeg")
axolotl.position.z = -5
axolotl.scale = glm.vec3(0.05, 0.05, 0.05)

rend.scene.append(axolotl)

isRunning = True

while isRunning:

	deltaTime = clock.tick(60) / 1000

	rend.elapsedTime += deltaTime

	keys = pygame.key.get_pressed()

	for event in pygame.event.get():
		if event.type == pygame.QUIT:
			isRunning = False

		elif event.type == pygame.KEYDOWN:

			# Reset/clear shader options
			if event.key == pygame.K_0:
				# Reset both: basic vertex + unlit fragment
				currVertexShader = vertex_shader
				currFragmentShader = unlit_fragment_shader
				rend.SetShaders(currVertexShader, currFragmentShader)

			if event.key == pygame.K_1:
				currFragmentShader = checker_fragment_shader
				rend.SetShaders(currVertexShader, currFragmentShader)

			if event.key == pygame.K_2:
				currFragmentShader = fresnel_fragment_shader
				rend.SetShaders(currVertexShader, currFragmentShader)

			if event.key == pygame.K_3:
				currFragmentShader = scanlines_fragment_shader
				rend.SetShaders(currVertexShader, currFragmentShader)

			if event.key == pygame.K_4:
				currFragmentShader = checker_fragment_shader
				rend.SetShaders(currVertexShader, currFragmentShader)

			if event.key == pygame.K_5:
				# Unlit fragment (clear fragment effects)
				currFragmentShader = unlit_fragment_shader
				rend.SetShaders(currVertexShader, currFragmentShader)


			if event.key == pygame.K_6:
				# Basic vertex (clear vertex effects)
				currVertexShader = vertex_shader
				rend.SetShaders(currVertexShader, currFragmentShader)

			if event.key == pygame.K_7:
				currVertexShader = twist_vertex_shader
				rend.SetShaders(currVertexShader, currFragmentShader)

			if event.key == pygame.K_8:
				currVertexShader = pulse_vertex_shader
				rend.SetShaders(currVertexShader, currFragmentShader)

			if event.key == pygame.K_9:
				currVertexShader = ripple_vertex_shader
				rend.SetShaders(currVertexShader, currFragmentShader)


	if keys[K_UP]:
		rend.camera.position.z += 1 * deltaTime

	if keys[K_DOWN]:
		rend.camera.position.z -= 1 * deltaTime

	if keys[K_RIGHT]:
		rend.camera.position.x += 1 * deltaTime

	if keys[K_LEFT]:
		rend.camera.position.x -= 1 * deltaTime


	# Camera rotation controls (degrees per second)
	rotSpeed = 60.0

	# Pitch (X axis): T/G
	if keys[K_t]:
		rend.camera.rotation.x += rotSpeed * deltaTime
	if keys[K_g]:
		rend.camera.rotation.x -= rotSpeed * deltaTime

	# Yaw (Y axis): F/H
	if keys[K_f]:
		rend.camera.rotation.y += rotSpeed * deltaTime
	if keys[K_h]:
		rend.camera.rotation.y -= rotSpeed * deltaTime

	# Roll (Z axis): R/Y
	if keys[K_r]:
		rend.camera.rotation.z += rotSpeed * deltaTime
	if keys[K_y]:
		rend.camera.rotation.z -= rotSpeed * deltaTime



	if keys[K_w]:
		rend.pointLight.z -= 10 * deltaTime

	if keys[K_s]:
		rend.pointLight.z += 10 * deltaTime

	if keys[K_a]:
		rend.pointLight.x -= 10 * deltaTime

	if keys[K_d]:
		rend.pointLight.x += 10 * deltaTime

	if keys[K_q]:
		rend.pointLight.y -= 10 * deltaTime

	if keys[K_e]:
		rend.pointLight.y += 10 * deltaTime


	if keys[K_z]:
		if rend.value > 0.0:
			rend.value -= 1 * deltaTime

	if keys[K_x]:
		if rend.value < 1.0:
			rend.value += 1 * deltaTime





	rend.Render()
	pygame.display.flip()

pygame.quit()