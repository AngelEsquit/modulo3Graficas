
class Obj(object):
	def __init__(self, filename):
		# Asumiendo que el archivo es un formato .obj
		with open(filename, "r") as file:
			lines = file.read().splitlines()
			
		self.vertices = []
		self.texCoords = []
		self.normals = []
		self.faces = []
		
		for line in lines:
			# Si la linea no cuenta con un prefijo y un valor,
			# seguimos a la siguiente la linea

			line = line.strip()
			if not line or line.startswith('#'):
				continue

			parts = line.split(None, 1)  # split on any whitespace, max 1
			if len(parts) == 0:
				continue
			prefix = parts[0]
			value = parts[1] if len(parts) > 1 else ''
			
			# Dependiendo del prefijo, parseamos y guardamos
			# la informacion en el contenedor correcto
			
			if prefix == "v": # Vertices
				# split on whitespace and ignore empty tokens
				tokens = [t for t in value.split() if t]
				if len(tokens) >= 3:
					vert = list(map(float, tokens[:3]))
					self.vertices.append(vert)
				
			elif prefix == "vt": # Coordenadas de textura
				tokens = [t for t in value.split() if t]
				if len(tokens) >= 2:
					vts = list(map(float, tokens[:2]))
					self.texCoords.append([vts[0], vts[1]])
				
			elif prefix == "vn": # Normales
				tokens = [t for t in value.split() if t]
				if len(tokens) >= 3:
					norm = list(map(float, tokens[:3]))
					self.normals.append(norm)
				
			elif prefix == "f": # Caras
				face = []
				# vertices can be separated by multiple spaces
				verts = [v for v in value.split() if v]
				for vert in verts:
					# vert can be 'v', 'v/vt', 'v//vn', or 'v/vt/vn'
					parts = vert.split('/')
					# convert to ints when present, use 0 when missing
					v_idx = int(parts[0]) if parts[0] != '' else 0
					vt_idx = int(parts[1]) if len(parts) > 1 and parts[1] != '' else 0
					vn_idx = int(parts[2]) if len(parts) > 2 and parts[2] != '' else 0
					face.append([v_idx, vt_idx, vn_idx])
				self.faces.append(face)