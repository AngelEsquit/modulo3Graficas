import pygame
import pygame.display
from pygame.locals import *

import glm
import math

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

pygame.display.set_caption("OpenGL Model Viewer - Lab 10")

rend = Renderer(screen)
rend.pointLight = glm.vec3(1,1,1)

# Default to new custom shaders
currVertexShader = vertex_shader
currFragmentShader = fragment_shader

rend.SetShaders(currVertexShader, currFragmentShader)

skyboxTextures = ["skybox/right.png",
				  "skybox/left.png",
				  "skybox/top.png",
				  "skybox/bottom.png",
				  "skybox/front.png",
				  "skybox/back.png"]

rend.CreateSkybox(skyboxTextures)


# ========== LOAD THREE MODELS ==========

# Model 1: Bucket Axolotl
model1 = Model("models/BucketAxolotl/Bucket_axolotl.obj")
model1.AddTexture("textures/BucketAxolotl/lucy.png")
model1.position = glm.vec3(0, 0, 0)
model1.scale = glm.vec3(0.05, 0.05, 0.05)

# Model 2: Yoshi
model2 = Model("models/Yoshi/yoshi.obj")
model2.AddTexture("textures/Yoshi/yoshi.png")
model2.position = glm.vec3(0, 0, 0)
model2.scale = glm.vec3(0.9, 0.9, 0.9)

# Model 3: Crash (multiple textures)
model3 = Model("models/Crash/crashbandicoot.obj")
# Crash uses multiple texture maps (color, shoes, back)
model3.AddTexture("textures/Crash/color_pallete.png")
model3.AddTexture("textures/Crash/shoes.png")
model3.AddTexture("textures/Crash/back.png")
model3.position = glm.vec3(0, -3, -10)
model3.scale = glm.vec3(0.01, 0.01, 0.01)

# Store all models in a list (Bucket, Yoshi, Crash)
allModels = [model1, model2, model3]
currentModelIndex = 0  # Start with first model

# Only add the current model to the scene
rend.scene.append(allModels[currentModelIndex])

# Setup orbital camera to look at the current model
rend.camera.SetTarget(allModels[currentModelIndex].position)
rend.camera.distance = 5.0
rend.camera.orbitMode = True

# Mouse control variables
mousePressed = False
mouseButton = None
lastMousePos = (0, 0)
mouseSensitivity = 0.005  # Radians per pixel (used for orbital)
freeMouseSensitivity = 0.005  # Radians per pixel mapped to degrees for free camera

isRunning = True

# Print controls to console
print("=" * 60)
print("OPENGL MODEL VIEWER - CONTROLS")
print("=" * 60)
print("\n--- MODEL SELECTION ---")
print("M / N: Switch between models (only one visible at a time)")
print("\n--- SHADERS ---")
print("Fragment Shaders:")
print("  0: Reset to default (basic lighting)")
print("  1: Checker pattern")
print("  2: Fresnel rim lighting")
print("  3: Scanlines effect")
print("  5: Unlit (no lighting)")
print("\nVertex Shaders:")
print("  6: Basic vertex shader")
print("  7: Twist effect")
print("  8: Pulse effect")
print("  9: Ripple effect")
print("\n--- CAMERA CONTROLS (ORBITAL MODE) ---")
print("Mouse:")
print("  Right-Click or Left-Click + Drag: Rotate around model")
print("  Mouse Wheel: Zoom in/out")
print("\nKeyboard:")
print("  Arrow Keys: Rotate around model")
print("  W/S: Move camera up/down (with limits)")
print("  A/D: Zoom in/out")
print("  C: Toggle camera mode (orbital/free)")
print("\n--- LIGHTING ---")
print("T/G: Move light Z")
print("F/H: Move light X")
print("R/Y: Move light Y")
print("\n--- OTHER ---")
print("Z/X: Adjust shader value parameter")
print("ESC or Close Window: Exit")
print("=" * 60)

while isRunning:

	deltaTime = clock.tick(60) / 1000

	rend.elapsedTime += deltaTime

	keys = pygame.key.get_pressed()

	for event in pygame.event.get():
		if event.type == pygame.QUIT:
			isRunning = False

		elif event.type == pygame.KEYDOWN:
			
			# Exit with ESC
			if event.key == pygame.K_ESCAPE:
				isRunning = False

			# ========== MODEL SWITCHING ==========
			if event.key == pygame.K_m:
				# Previous model
				rend.scene.clear()
				currentModelIndex = (currentModelIndex - 1) % len(allModels)
				rend.scene.append(allModels[currentModelIndex])
				rend.camera.SetTarget(allModels[currentModelIndex].position)
				print(f"Switched to Model {currentModelIndex + 1}")

			if event.key == pygame.K_n:
				# Next model
				rend.scene.clear()
				currentModelIndex = (currentModelIndex + 1) % len(allModels)
				rend.scene.append(allModels[currentModelIndex])
				rend.camera.SetTarget(allModels[currentModelIndex].position)
				print(f"Switched to Model {currentModelIndex + 1}")

			# ========== CAMERA MODE ==========
			if event.key == pygame.K_c:
				rend.camera.ToggleCameraMode()
				mode = "Orbital" if rend.camera.orbitMode else "Free"
				print(f"Camera Mode: {mode}")

			# ========== SHADER SELECTION ==========
			# Fragment shaders
			if event.key == pygame.K_0:
				# Reset both: basic vertex + basic fragment
				currVertexShader = vertex_shader
				currFragmentShader = fragment_shader
				rend.SetShaders(currVertexShader, currFragmentShader)
				print("Shaders: Default (basic lighting)")

			if event.key == pygame.K_1:
				currFragmentShader = checker_fragment_shader
				rend.SetShaders(currVertexShader, currFragmentShader)
				print("Fragment Shader: Checker pattern")

			if event.key == pygame.K_2:
				currFragmentShader = fresnel_fragment_shader
				rend.SetShaders(currVertexShader, currFragmentShader)
				print("Fragment Shader: Fresnel rim lighting")

			if event.key == pygame.K_3:
				currFragmentShader = scanlines_fragment_shader
				rend.SetShaders(currVertexShader, currFragmentShader)
				print("Fragment Shader: Scanlines")

			if event.key == pygame.K_5:
				# Unlit fragment (clear fragment effects)
				currFragmentShader = unlit_fragment_shader
				rend.SetShaders(currVertexShader, currFragmentShader)
				print("Fragment Shader: Unlit")

			# Vertex shaders
			if event.key == pygame.K_6:
				# Basic vertex (clear vertex effects)
				currVertexShader = vertex_shader
				rend.SetShaders(currVertexShader, currFragmentShader)
				print("Vertex Shader: Basic")

			if event.key == pygame.K_7:
				currVertexShader = twist_vertex_shader
				rend.SetShaders(currVertexShader, currFragmentShader)
				print("Vertex Shader: Twist")

			if event.key == pygame.K_8:
				currVertexShader = pulse_vertex_shader
				rend.SetShaders(currVertexShader, currFragmentShader)
				print("Vertex Shader: Pulse")

			if event.key == pygame.K_9:
				currVertexShader = ripple_vertex_shader
				rend.SetShaders(currVertexShader, currFragmentShader)
				print("Vertex Shader: Ripple")

		# ========== MOUSE CONTROLS ==========
		elif event.type == pygame.MOUSEBUTTONDOWN:
			# Support left (1) or right (3) click for rotation
			if event.button == 1 or event.button == 3:
				mousePressed = True
				mouseButton = event.button
				lastMousePos = pygame.mouse.get_pos()
				pygame.mouse.set_visible(False)
			elif event.button == 4:  # Mouse wheel up (zoom in)
				rend.camera.Zoom(-0.5)
			elif event.button == 5:  # Mouse wheel down (zoom out)
				rend.camera.Zoom(0.5)

		elif event.type == pygame.MOUSEBUTTONUP:
			if event.button == 1 or event.button == 3:
				mousePressed = False
				mouseButton = None
				pygame.mouse.set_visible(True)

		elif event.type == pygame.MOUSEMOTION:
			if mousePressed:
				currentMousePos = pygame.mouse.get_pos()
				deltaX = currentMousePos[0] - lastMousePos[0]
				deltaY = currentMousePos[1] - lastMousePos[1]
				
				if rend.camera.orbitMode:
					# Orbital camera: rotate around target
					rend.camera.OrbitHorizontal(deltaX * mouseSensitivity)
					# Vertical rotation (pitch) - inverted for natural feel
					rend.camera.OrbitVertical(-deltaY * mouseSensitivity)
				else:
					# Free camera: adjust Euler angles (degrees)
					deg_per_pixel = mouseSensitivity * (180.0 / 3.14159265)
					rend.camera.rotation.y += -deltaX * deg_per_pixel
					rend.camera.rotation.x += -deltaY * deg_per_pixel
				
				lastMousePos = currentMousePos


	# ========== KEYBOARD CAMERA CONTROLS ==========
	if rend.camera.orbitMode:
		# Orbital camera controls
		orbitSpeed = 1.5  # radians per second
		zoomSpeed = 4.0   # units per second
		verticalSpeed = 1.5  # radians per second for vertical movement

		# Arrow keys: Rotate around model
		if keys[K_LEFT]:
			rend.camera.OrbitHorizontal(orbitSpeed * deltaTime)
		if keys[K_RIGHT]:
			rend.camera.OrbitHorizontal(-orbitSpeed * deltaTime)
		if keys[K_UP]:
			rend.camera.OrbitVertical(verticalSpeed * deltaTime)
		if keys[K_DOWN]:
			rend.camera.OrbitVertical(-verticalSpeed * deltaTime)

		# W/S: Move camera up and down (with limits)
		if keys[K_w]:
			rend.camera.OrbitVertical(verticalSpeed * deltaTime)
		if keys[K_s]:
			rend.camera.OrbitVertical(-verticalSpeed * deltaTime)

		# A/D: Zoom in and out
		if keys[K_a]:
			rend.camera.Zoom(-zoomSpeed * deltaTime)
		if keys[K_d]:
			rend.camera.Zoom(zoomSpeed * deltaTime)

	else:
		# Free camera mode (original behavior)
		moveSpeed = 1.3
		identity = glm.mat4(1)
		pitchMat = glm.rotate(identity, glm.radians(rend.camera.rotation.x), glm.vec3(1,0,0))
		yawMat   = glm.rotate(identity, glm.radians(rend.camera.rotation.y), glm.vec3(0,1,0))
		rollMat  = glm.rotate(identity, glm.radians(rend.camera.rotation.z), glm.vec3(0,0,1))
		rotationMat = pitchMat * yawMat * rollMat

		# Local axes in world space
		right   = glm.normalize(glm.vec3(rotationMat * glm.vec4(1,0,0,0)))
		up      = glm.normalize(glm.vec3(rotationMat * glm.vec4(0,1,0,0)))
		forward = glm.normalize(glm.vec3(rotationMat * glm.vec4(0,0,-1,0)))

		if keys[K_UP]:
			rend.camera.position += forward * (moveSpeed * deltaTime)

		if keys[K_DOWN]:
			rend.camera.position -= forward * (moveSpeed * deltaTime)

		if keys[K_RIGHT]:
			rend.camera.position += right * (moveSpeed * deltaTime)

		if keys[K_LEFT]:
			rend.camera.position -= right * (moveSpeed * deltaTime)

		# Camera rotation controls (degrees per second)
		rotSpeed = 35.0

		# Pitch (X axis): W/S
		if keys[K_w]:
			rend.camera.rotation.x += rotSpeed * deltaTime
		if keys[K_s]:
			rend.camera.rotation.x -= rotSpeed * deltaTime

		# Yaw (Y axis): A/D
		if keys[K_a]:
			rend.camera.rotation.y += rotSpeed * deltaTime
		if keys[K_d]:
			rend.camera.rotation.y -= rotSpeed * deltaTime

		# Roll (Z axis): Q/E
		if keys[K_q]:
			rend.camera.rotation.z += rotSpeed * deltaTime
		if keys[K_e]:
			rend.camera.rotation.z -= rotSpeed * deltaTime



	if keys[K_t]:
		rend.pointLight.z -= 10 * deltaTime

	if keys[K_g]:
		rend.pointLight.z += 10 * deltaTime

	if keys[K_f]:
		rend.pointLight.x -= 10 * deltaTime

	if keys[K_h]:
		rend.pointLight.x += 10 * deltaTime

	if keys[K_r]:
		rend.pointLight.y -= 10 * deltaTime

	if keys[K_y]:
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