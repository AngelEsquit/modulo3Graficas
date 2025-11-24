
from pathlib import Path

from mtl import parse_mtl_file


class Obj(object):
	def __init__(self, filename):
		self.filepath = Path(filename)
		with self.filepath.open("r", encoding="utf-8", errors="ignore") as file:
			lines = file.read().splitlines()
		
		self.vertices = []
		self.texCoords = []
		self.normals = []
		self.faces = []
		self.faceMaterials = []
		self.materials = {}
		self.materialLibraries = []

		currentMaterial = None

		for line in lines:
			line = line.strip()
			if not line or line.startswith('#'):
				continue

			parts = line.split(None, 1)
			if len(parts) == 0:
				continue
			prefix = parts[0]
			value = parts[1] if len(parts) > 1 else ''

			if prefix == "v":
				tokens = [t for t in value.split() if t]
				if len(tokens) >= 3:
					vert = list(map(float, tokens[:3]))
					self.vertices.append(vert)

			elif prefix == "vt":
				tokens = [t for t in value.split() if t]
				if len(tokens) >= 2:
					vts = list(map(float, tokens[:2]))
					self.texCoords.append([vts[0], vts[1]])

			elif prefix == "vn":
				tokens = [t for t in value.split() if t]
				if len(tokens) >= 3:
					norm = list(map(float, tokens[:3]))
					self.normals.append(norm)

			elif prefix == "mtllib":
				self._load_material_library(value)

			elif prefix == "usemtl":
				currentMaterial = value.strip() or None

			elif prefix == "f":
				face = []
				verts = [v for v in value.split() if v]
				for vert in verts:
					parts = vert.split('/')
					v_idx = int(parts[0]) if parts[0] != '' else 0
					vt_idx = int(parts[1]) if len(parts) > 1 and parts[1] != '' else 0
					vn_idx = int(parts[2]) if len(parts) > 2 and parts[2] != '' else 0
					face.append([v_idx, vt_idx, vn_idx])
				self.faces.append(face)
				self.faceMaterials.append(currentMaterial)

	def _load_material_library(self, value):
		candidates = self._resolve_mtllib_values(value)
		for candidate in candidates:
			try:
				materials = parse_mtl_file(candidate)
			except FileNotFoundError:
				continue
			self.materialLibraries.append(str(candidate))
			for name, data in materials.items():
				self.materials[name] = data

	def _resolve_mtllib_values(self, raw_value):
		value = raw_value.strip()
		if not value:
			return []

		primary = (self.filepath.parent / value).resolve()
		if primary.exists():
			return [primary]

		absolute = Path(value)
		if absolute.exists():
			return [absolute.resolve()]

		paths = []
		for token in value.split():
			token_path = Path(token)
			if not token_path.is_absolute():
				token_path = (self.filepath.parent / token).resolve()
			paths.append(token_path)
		return paths