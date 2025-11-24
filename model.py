from OpenGL.GL import *
from obj import Obj
from buffer import Buffer

import glm

import pygame
from pathlib import Path
import math


class _MaterialGroup(object):
	def __init__(self, name, material, *, udim_tile=None):
		self.name = name
		self.material = material or {}
		self.udimTile = udim_tile
		self.udimTileNumber = None
		if self.udimTile is not None:
			u_tile, v_tile = self.udimTile
			self.udimTileNumber = 1001 + u_tile + (v_tile * 10)

		self.positions = []
		self.texCoords = []
		self.normals = []
		self.vertexCount = 0
		self.posBuffer = None
		self.texCoordsBuffer = None
		self.normalsBuffer = None
		self.texture = None
		self.diffuseColor = self.material.get("Kd")
		self._fallbackTexture = None

	def append_vertex(self, position, texCoord, normal):
		for value in position:
			self.positions.append(value)
		for value in texCoord:
			self.texCoords.append(value)
		for value in normal:
			self.normals.append(value)
		self.vertexCount += 1

	def finalize(self):
		if self.vertexCount == 0:
			return False
		self.posBuffer = Buffer(self.positions)
		self.texCoordsBuffer = Buffer(self.texCoords)
		self.normalsBuffer = Buffer(self.normals)
		return True


class Model(object):
	_texture_cache = {}
	_color_texture_cache = {}

	def __init__(self, filename, name=None):
		self.objFile = Obj(filename)

		self.name = name or Path(filename).stem

		self.position = glm.vec3(0,0,0)
		self.rotation = glm.vec3(0,0,0)
		self.scale = glm.vec3(1,1,1)
		self.cameraFocusDistance = None
		self.shaderValue = 0.0

		self.materialGroups = []
		self.vertexCount = 0
		self.sourceBoundsMin = glm.vec3(0, 0, 0)
		self.sourceBoundsMax = glm.vec3(0, 0, 0)
		self.sourceBoundsSize = glm.vec3(0, 0, 0)
		self.sourceBoundsCenter = glm.vec3(0, 0, 0)
		self.sourceBoundsRadius = 0.0
		self.materialUsesUDIM = self._detect_udim_materials()

		self.textures = []
		self.shaderProgram = None

		self.posBuffer = None
		self.texCoordsBuffer = None
		self.normalsBuffer = None

		self._compute_source_bounds()
		self.BuildBuffers()

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

		self.materialGroups = []
		self.vertexCount = 0
		self.posBuffer = None
		self.texCoordsBuffer = None
		self.normalsBuffer = None

		groups = {}

		def get_group(material_name, tile_key=None):
			key = (material_name, tile_key)
			if key not in groups:
				material = self.objFile.materials.get(material_name) if material_name else {}
				groups[key] = _MaterialGroup(material_name, material, udim_tile=tile_key)
			return groups[key]

		for face_index, face in enumerate(self.objFile.faces):
			material_name = None
			if face_index < len(self.objFile.faceMaterials):
				material_name = self.objFile.faceMaterials[face_index]

			has_uv = bool(self.objFile.texCoords)
			uses_udim = has_uv and self._material_uses_udim(material_name)
			face_tile_key = None

			facePositions = []
			faceTexCoords = []
			faceNormals = []

			for i in range(len(face)):
				v_idx = face[i][0] - 1 if len(face[i]) >= 1 and face[i][0] != 0 else None
				vt_idx = face[i][1] - 1 if len(face[i]) >= 2 and face[i][1] != 0 else None
				vn_idx = face[i][2] - 1 if len(face[i]) >= 3 and face[i][2] != 0 else None

				if v_idx is None or v_idx >= len(self.objFile.vertices):
					continue
				facePositions.append(self.objFile.vertices[v_idx])

				if vt_idx is not None and vt_idx < len(self.objFile.texCoords):
					u, v = self.objFile.texCoords[vt_idx]
					if uses_udim:
						tile_u = int(math.floor(u))
						tile_v = int(math.floor(v))
						tile_key = (tile_u, tile_v)
						if face_tile_key is None:
							face_tile_key = tile_key
						elif face_tile_key != tile_key:
							print(f"[Model] UDIM face spans multiple tiles for material '{material_name}', using first tile {face_tile_key}.")
						u -= tile_u
						v -= tile_v
					faceTexCoords.append([u, v])
				else:
					faceTexCoords.append([0.0, 0.0])

				if vn_idx is not None and vn_idx < len(self.objFile.normals):
					faceNormals.append(self.objFile.normals[vn_idx])
				else:
					faceNormals.append(None)

			group = get_group(material_name, face_tile_key if uses_udim else None)

			if any(n is None for n in faceNormals):
				if len(facePositions) >= 3:
					p0 = facePositions[0]
					p1 = facePositions[1]
					p2 = facePositions[2]
					ux = p1[0] - p0[0]; uy = p1[1] - p0[1]; uz = p1[2] - p0[2]
					vx = p2[0] - p0[0]; vy = p2[1] - p0[1]; vz = p2[2] - p0[2]
					nx = uy * vz - uz * vy
					ny = uz * vx - ux * vz
					nz = ux * vy - uy * vx
					length = (nx * nx + ny * ny + nz * nz) ** 0.5
					if length == 0:
						fn = [0.0, 1.0, 0.0]
					else:
						fn = [nx / length, ny / length, nz / length]
					for idx in range(len(faceNormals)):
						if faceNormals[idx] is None:
							faceNormals[idx] = fn
				else:
					for idx in range(len(faceNormals)):
						if faceNormals[idx] is None:
							faceNormals[idx] = [0.0, 1.0, 0.0]

			num_vertices = len(facePositions)
			if num_vertices < 3:
				continue

			for tri_idx in range(1, num_vertices - 1):
				indices = (0, tri_idx, tri_idx + 1)
				for idx in indices:
					group.append_vertex(facePositions[idx], faceTexCoords[idx], faceNormals[idx])

		self.materialGroups = []
		self.vertexCount = 0

		for group in groups.values():
			if not group.finalize():
				continue
			self._assign_material_texture(group)
			self.materialGroups.append(group)
			self.vertexCount += group.vertexCount

		if len(self.materialGroups) == 1:
			single = self.materialGroups[0]
			self.posBuffer = single.posBuffer
			self.texCoordsBuffer = single.texCoordsBuffer
			self.normalsBuffer = single.normalsBuffer

	def AddTexture(self, filename):
		texture = self._load_texture_from_path(filename)
		if texture is not None:
			self.textures.append(texture)
		return texture


	def SetShaderProgram(self, shaderProgram):
		self.shaderProgram = shaderProgram


	def GetFocusPoint(self):
		return glm.vec3(self.position)


	def Render(self):

		if not self.materialGroups:
			return

		for group in self.materialGroups:
			self._bind_textures_for_group(group)

			group.posBuffer.Use(0, 3)
			group.texCoordsBuffer.Use(1, 2)
			group.normalsBuffer.Use(2, 3)

			glDrawArrays(GL_TRIANGLES, 0, group.vertexCount)

			glDisableVertexAttribArray(0)
			glDisableVertexAttribArray(1)
			glDisableVertexAttribArray(2)


	def _bind_textures_for_group(self, group):
		texture_id = group.texture or group._fallbackTexture
		if texture_id is None:
			texture_id = self._ensure_color_texture(group)

		if texture_id is not None:
			glActiveTexture(GL_TEXTURE0)
			glBindTexture(GL_TEXTURE_2D, texture_id)
			for i in range(1, len(self.textures)):
				glActiveTexture(GL_TEXTURE0 + i)
				glBindTexture(GL_TEXTURE_2D, 0)
		elif self.textures:
			for i in range(len(self.textures)):
				glActiveTexture(GL_TEXTURE0 + i)
				glBindTexture(GL_TEXTURE_2D, self.textures[i])
		else:
			glActiveTexture(GL_TEXTURE0)
			glBindTexture(GL_TEXTURE_2D, 0)


	def _assign_material_texture(self, group):
		diffuse = group.material.get("map_Kd_path") or group.material.get("map_Kd")
		if diffuse:
			if group.udimTile is not None and "<UDIM>" in diffuse:
				udim_number = group.udimTileNumber or 1001
				candidate = diffuse.replace("<UDIM>", f"{udim_number:04d}")
				texture = self._load_texture_cached(candidate)
				if texture is not None:
					group.texture = texture
					return
			else:
				for candidate in self._iter_texture_candidates(diffuse):
					texture = self._load_texture_cached(candidate)
					if texture is not None:
						group.texture = texture
						return
		elif group.diffuseColor:
			group._fallbackTexture = self._get_color_texture(tuple(group.diffuseColor))


	def _load_texture_from_path(self, filename):
		try:
			surface = pygame.image.load(str(filename))
		except Exception as exc:
			print(f"[Model] Could not load texture '{filename}': {exc}")
			return None
		return self._surface_to_texture(surface)


	@classmethod
	def _load_texture_cached(cls, filename):
		path = Path(filename)
		try:
			key = str(path.resolve())
		except Exception:
			key = str(filename)

		if key in cls._texture_cache:
			return cls._texture_cache[key]

		try:
			surface = pygame.image.load(key)
		except Exception as exc:
			print(f"[MTL] Could not load texture '{filename}': {exc}")
			return None

		texture = cls._surface_to_texture(surface)
		cls._texture_cache[key] = texture
		return texture


	@staticmethod
	def _surface_to_texture(surface):
		textureData = pygame.image.tostring(surface, "RGB", True)

		texture = glGenTextures(1)
		glBindTexture(GL_TEXTURE_2D, texture)

		glTexImage2D(GL_TEXTURE_2D,
					 0,
					 GL_RGB,
					 surface.get_width(),
					 surface.get_height(),
					 0,
					 GL_RGB,
					 GL_UNSIGNED_BYTE,
					 textureData)

		glGenerateMipmap(GL_TEXTURE_2D)
		return texture


	@classmethod
	def _get_color_texture(cls, color):
		if not color:
			return cls._get_default_white()

		key = tuple(round(max(0.0, min(1.0, component)), 3) for component in color[:3])

		if key in cls._color_texture_cache:
			return cls._color_texture_cache[key]

		surface = pygame.Surface((1, 1))
		surface.fill(tuple(int(component * 255) for component in key))
		texture = cls._surface_to_texture(surface)
		cls._color_texture_cache[key] = texture
		return texture


	@classmethod
	def _get_default_white(cls):
		if "__white__" in cls._color_texture_cache:
			return cls._color_texture_cache["__white__"]

		surface = pygame.Surface((1, 1))
		surface.fill((255, 255, 255))
		texture = cls._surface_to_texture(surface)
		cls._color_texture_cache["__white__"] = texture
		return texture


	def _ensure_color_texture(self, group):
		if group.diffuseColor:
			group._fallbackTexture = self._get_color_texture(tuple(group.diffuseColor))
			return group._fallbackTexture
		return self._get_default_white()


	def _iter_texture_candidates(self, texture_path):
		path = Path(texture_path)
		if "<UDIM>" not in str(path):
			yield str(path)
			return

		try:
			path = path.resolve()
		except Exception:
			path = Path(texture_path)

		pattern = path.name.replace("<UDIM>", "????")
		matches = sorted(path.parent.glob(pattern))
		if not matches:
			print(f"[MTL] No UDIM tiles found for pattern: {path}")
			return

		for match in matches:
			yield str(match)


	def _detect_udim_materials(self):
		result = {}
		for name, material in self.objFile.materials.items():
			path = material.get("map_Kd_path") or material.get("map_Kd") or ""
			result[name] = "<UDIM>" in str(path)
		return result


	def _material_uses_udim(self, material_name):
		if material_name is None:
			return False
		return self.materialUsesUDIM.get(material_name, False)


	def _compute_source_bounds(self):
		if not self.objFile.vertices:
			self.sourceBoundsMin = glm.vec3(0, 0, 0)
			self.sourceBoundsMax = glm.vec3(0, 0, 0)
			self.sourceBoundsSize = glm.vec3(0, 0, 0)
			self.sourceBoundsCenter = glm.vec3(0, 0, 0)
			self.sourceBoundsRadius = 0.0
			return

		mins = [min(vertex[i] for vertex in self.objFile.vertices) for i in range(3)]
		maxs = [max(vertex[i] for vertex in self.objFile.vertices) for i in range(3)]

		self.sourceBoundsMin = glm.vec3(*mins)
		self.sourceBoundsMax = glm.vec3(*maxs)
		self.sourceBoundsSize = self.sourceBoundsMax - self.sourceBoundsMin
		self.sourceBoundsCenter = self.sourceBoundsMin + (self.sourceBoundsSize * 0.5)
		self.sourceBoundsRadius = glm.length(self.sourceBoundsSize) * 0.5

	def GetScaledBoundsSize(self):
		return glm.vec3(
			self.sourceBoundsSize.x * self.scale.x,
			self.sourceBoundsSize.y * self.scale.y,
			self.sourceBoundsSize.z * self.scale.z,
		)

	def GetScaledRadius(self):
		scaled_size = self.GetScaledBoundsSize()
		return glm.length(scaled_size) * 0.5




