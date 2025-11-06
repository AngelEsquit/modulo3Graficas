import glm
import math

class Camera(object):
	def __init__(self, width, height):

		self.screenWidth = width
		self.screenHeight = height

		self.position = glm.vec3(0, 10, 0)

		# Angulos de Euler
		self.rotation = glm.vec3(0,0,0)

		self.viewMatrix = None

		# Orbital camera parameters
		self.orbitMode = True  # Toggle between free and orbital camera
		self.target = glm.vec3(0, 0, 0)  # Point the camera looks at
		self.distance = 5.0  # Distance from target
		self.minDistance = 1.5
		self.maxDistance = 20.0
		
		# Orbital angles (in radians for precision)
		self.orbitAngleY = 0.0  # Horizontal rotation (azimuth)
		self.orbitAngleX = 0.3  # Vertical rotation (elevation), starting slightly above
		self.minOrbitAngleX = -math.pi * 0.45  # -85 degrees (don't go too low)
		self.maxOrbitAngleX = math.pi * 0.45   # +85 degrees (don't go too high)

		self.CreateProjectionMatrix(60, 0.1, 1000)


	def Update(self):
		if self.orbitMode:
			# Orbital camera: position based on spherical coordinates around target
			# Clamp vertical angle
			self.orbitAngleX = max(self.minOrbitAngleX, min(self.maxOrbitAngleX, self.orbitAngleX))
			
			# Calculate position in spherical coordinates
			x = self.target.x + self.distance * math.cos(self.orbitAngleX) * math.sin(self.orbitAngleY)
			y = self.target.y + self.distance * math.sin(self.orbitAngleX)
			z = self.target.z + self.distance * math.cos(self.orbitAngleX) * math.cos(self.orbitAngleY)
			
			self.position = glm.vec3(x, y, z)
			
			# Create view matrix looking at target
			self.viewMatrix = glm.lookAt(self.position, self.target, glm.vec3(0, 1, 0))
		else:
			# Free camera mode (original behavior)
			identity = glm.mat4(1)

			translateMat = glm.translate(identity, self.position)

			pitchMat = glm.rotate(identity, glm.radians(self.rotation.x), glm.vec3(1,0,0))
			yawMat =   glm.rotate(identity, glm.radians(self.rotation.y), glm.vec3(0,1,0))
			rollMat =  glm.rotate(identity, glm.radians(self.rotation.z), glm.vec3(0,0,1))

			rotationMat = pitchMat * yawMat * rollMat

			camMat = translateMat * rotationMat

			self.viewMatrix = glm.inverse(camMat)


	def OrbitHorizontal(self, angle):
		"""Rotate camera horizontally around target (in radians)"""
		if self.orbitMode:
			self.orbitAngleY += angle


	def OrbitVertical(self, angle):
		"""Rotate camera vertically around target (in radians)"""
		if self.orbitMode:
			self.orbitAngleX += angle
			# Clamping is done in Update()


	def Zoom(self, delta):
		"""Zoom in/out by changing distance from target"""
		if self.orbitMode:
			self.distance += delta
			self.distance = max(self.minDistance, min(self.maxDistance, self.distance))


	def SetTarget(self, target):
		"""Set the point the camera orbits around"""
		self.target = glm.vec3(target)


	def ToggleCameraMode(self):
		"""Switch between orbital and free camera"""
		self.orbitMode = not self.orbitMode


	def CreateProjectionMatrix(self, fov, nearPlane, farPlane):
		self.projectionMatrix = glm.perspective( glm.radians(fov), self.screenWidth / self.screenHeight, nearPlane, farPlane)