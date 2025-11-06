from OpenGL.GL import *
from obj import Obj
from buffer import Buffer

import glm

import pygame

class Model(object):
	def __init__(self, filename):
		self.objFile = Obj(filename)

		self.position = glm.vec3(0,0,0)
		self.rotation = glm.vec3(0,0,0)
		self.scale = glm.vec3(1,1,1)

		self.BuildBuffers()

		self.textures = []

	def GetModelMatrix(self):

		identity = glm.mat4(1)

		translateMat = glm.translate(identity, self.position)

		pitchMat = glm.rotate(identity, glm.radians(self.rotation.x), glm.vec3(1,0,0))
		yawMat =   glm.rotate(identity, glm.radians(self.rotation.y), glm.vec3(0,1,0))
		rollMat =  glm.rotate(identity, glm.radians(self.rotation.z), glm.vec3(0,0,1))

		rotationMat = pitchMat * yawMat * rollMat

		scaleMat = glm.scale(identity, self.scale)

		return translateMat * rotationMat * scaleMat


	def BuildBuffers(self):

		positions = []
		texCoords = []
		normals = []

		self.vertexCount = 0

		for face in self.objFile.faces:

			# Collect per-vertex data for this face handling missing vt or vn entries
			facePositions = []
			faceTexCoords = []
			faceNormals = []

			# Helper to safely get indices (OBJ uses 1-based indices)
			for i in range(len(face)):
				v_idx = face[i][0] - 1 if len(face[i]) >= 1 and face[i][0] != 0 else None
				vt_idx = face[i][1] - 1 if len(face[i]) >= 2 and face[i][1] != 0 else None
				vn_idx = face[i][2] - 1 if len(face[i]) >= 3 and face[i][2] != 0 else None

				# Position is mandatory in most OBJ files; skip vertex if missing
				if v_idx is None:
					continue
				facePositions.append(self.objFile.vertices[v_idx])

				# Texcoords may be missing
				if vt_idx is not None and vt_idx < len(self.objFile.texCoords):
					faceTexCoords.append(self.objFile.texCoords[vt_idx])
				else:
					faceTexCoords.append([0.0, 0.0])

				# Normals may be missing; use None as placeholder
				if vn_idx is not None and vn_idx < len(self.objFile.normals):
					faceNormals.append(self.objFile.normals[vn_idx])
				else:
					faceNormals.append(None)

			# If any normal is missing, compute face normal from the first three positions
			if any(n is None for n in faceNormals):
				# Need at least 3 positions to compute normal
				if len(facePositions) >= 3:
					p0 = facePositions[0]
					p1 = facePositions[1]
					p2 = facePositions[2]
					# compute vectors
					ux = p1[0] - p0[0]; uy = p1[1] - p0[1]; uz = p1[2] - p0[2]
					vx = p2[0] - p0[0]; vy = p2[1] - p0[1]; vz = p2[2] - p0[2]
					# cross product u x v
					nx = uy * vz - uz * vy
					ny = uz * vx - ux * vz
					nz = ux * vy - uy * vx
					# normalize
					length = (nx * nx + ny * ny + nz * nz) ** 0.5
					if length == 0:
						fn = [0.0, 1.0, 0.0]
					else:
						fn = [nx / length, ny / length, nz / length]
					# replace None normals with face normal
					for idx in range(len(faceNormals)):
						if faceNormals[idx] is None:
							faceNormals[idx] = fn
				else:
					# Fallback normal if insufficient vertices
					for idx in range(len(faceNormals)):
						if faceNormals[idx] is None:
							faceNormals[idx] = [0.0, 1.0, 0.0]

			# Append triangle vertices (triangulate quads if necessary)

			def append_vertex_triplet(p, t, n):
				for value in p: positions.append(value)
				for value in t: texCoords.append(value)
				for value in n: normals.append(value)

			# Triangles: straightforward
			if len(facePositions) >= 3:
				append_vertex_triplet(facePositions[0], faceTexCoords[0], faceNormals[0])
				append_vertex_triplet(facePositions[1], faceTexCoords[1], faceNormals[1])
				append_vertex_triplet(facePositions[2], faceTexCoords[2], faceNormals[2])
				self.vertexCount += 3

			# If face is a quad (4 vertices), create second triangle 0,2,3
			if len(facePositions) == 4:
				append_vertex_triplet(facePositions[0], faceTexCoords[0], faceNormals[0])
				append_vertex_triplet(facePositions[2], faceTexCoords[2], faceNormals[2])
				append_vertex_triplet(facePositions[3], faceTexCoords[3], faceNormals[3])
				self.vertexCount += 3


		self.posBuffer = Buffer(positions)
		self.texCoordsBuffer = Buffer(texCoords)
		self.normalsBuffer = Buffer(normals)


	def AddTexture(self, filename):
		textureSurface = pygame.image.load(filename)
		textureData = pygame.image.tostring(textureSurface, "RGB", True)

		texture = glGenTextures(1)
		glBindTexture(GL_TEXTURE_2D, texture)

		glTexImage2D(GL_TEXTURE_2D,
					 0,
					 GL_RGB,
					 textureSurface.get_width(),
					 textureSurface.get_height(),
					 0,
					 GL_RGB,
					 GL_UNSIGNED_BYTE,
					 textureData)

		glGenerateMipmap(GL_TEXTURE_2D)

		self.textures.append(texture)


	def Render(self):

		# Dar la textura
		for i in range(len(self.textures)):
			glActiveTexture(GL_TEXTURE0 + i)
			glBindTexture(GL_TEXTURE_2D, self.textures[i])


		self.posBuffer.Use(0, 3)
		self.texCoordsBuffer.Use(1, 2)
		self.normalsBuffer.Use(2, 3)


		glDrawArrays(GL_TRIANGLES, 0, self.vertexCount)

		glDisableVertexAttribArray(0)
		glDisableVertexAttribArray(1)
		glDisableVertexAttribArray(2)




