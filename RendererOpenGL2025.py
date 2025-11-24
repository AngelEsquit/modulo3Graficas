import os
import pygame
import pygame.display

import glm

from gl import Renderer
from model import Model
from scene_controller import SceneController
from vertexShaders import (
	vertex_shader,
	twist_vertex_shader,
	pulse_vertex_shader,
	ripple_vertex_shader,
	decal_vertex_shader,
)
from fragmentShaders import (
	fragment_shader,
	checker_fragment_shader,
	fresnel_fragment_shader,
	scanlines_fragment_shader,
	unlit_fragment_shader,
	decal_fragment_shader,
)


WIDTH = 900
HEIGHT = 576
ENABLE_SAMPLE_CONTENT = True


class DioramaApp:
	def __init__(self, width=WIDTH, height=HEIGHT):
		pygame.init()
		self.screen = pygame.display.set_mode((width, height), pygame.DOUBLEBUF | pygame.OPENGL)
		self.clock = pygame.time.Clock()
		pygame.display.set_caption("OpenGL Diorama Toolkit")

		self.renderer = Renderer(self.screen)
		self.renderer.LoadMaskTexture("assets/Logo.png")
		self.renderer.pointLight = glm.vec3(1, 1, 1)
		self.scene = SceneController(self.renderer)

		self.music_path = os.path.join("assets", "Spider-Man 1967 Cartoon Theme Song.mp3")
		self._init_audio()

		self.shader_baseline_value = 0.0
		self.preset_active = False

		self.running = True
		self.delta_time = 0.0
		self.keys = None

		self.mouse_pressed = False
		self.mouse_button = None
		self.last_mouse_pos = (0, 0)
		self.mouse_sensitivity = 0.005

		self.vertex_shaders = {
			"basic": vertex_shader,
			"twist": twist_vertex_shader,
			"pulse": pulse_vertex_shader,
			"ripple": ripple_vertex_shader,
			"decal": decal_vertex_shader,
		}

		self.fragment_shaders = {
			"basic": fragment_shader,
			"checker": checker_fragment_shader,
			"fresnel": fresnel_fragment_shader,
			"scanlines": scanlines_fragment_shader,
			"unlit": unlit_fragment_shader,
			"decal": decal_fragment_shader,
		}

		self.default_vertex_key = "basic"
		self.default_fragment_key = "basic"
		self.renderer.SetShaders(
			self.vertex_shaders[self.default_vertex_key],
			self.fragment_shaders[self.default_fragment_key],
		)

		self.skybox_textures = [
			"skybox/right.png",
			"skybox/left.png",
			"skybox/top.png",
			"skybox/bottom.png",
			"skybox/front.png",
			"skybox/back.png",
		]
		self.renderer.CreateSkybox(self.skybox_textures)

		self.model_shader_state = {}

		if ENABLE_SAMPLE_CONTENT:
			self._load_sample_models()

		self._print_controls()

	def run(self):
		while self.running:
			self.delta_time = self.clock.tick(45) / 1000
			self.renderer.elapsedTime += self.delta_time
			self.keys = pygame.key.get_pressed()
			self._process_events()
			self._update_camera()
			self._update_lights()
			self._update_shader_value()
			self.renderer.Render()
			pygame.display.flip()

		self._shutdown_audio()
		pygame.quit()

	def _print_controls(self):
		print("=" * 64)
		print("OPENGL DIORAMA TOOLKIT - CONTROLS")
		print("=" * 64)
		print("\n--- MODEL FOCUS ---")
		print("M / N: Focus previous/next registered model")
		print("\n--- SHADERS (apply to focused model) ---")
		print("0: Reset to defaults (basic vertex + fragment)")
		print("Fragment: 1=Checker, 2=Fresnel, 3=Scanlines, 5=Unlit (toggle)")
		print("Vertex: 6=Basic, 7=Twist, 8=Pulse, 9=Ripple (toggle)")
		print("4: Apply decal shader (vertex+fragment)")
		print("P: Toggle preset shader look")
		print("\n--- CAMERA ---")
		print("Mouse drag: orbit / look around")
		print("Mouse wheel or A/D: zoom (orbital)")
		print("Arrow keys / W S: orbit vertical")
		print("C: Toggle orbital vs free camera")
		print("\n--- LIGHTING ---")
		print("T/G, F/H, R/Y: move point light along Z, X, Y")
		print("\n--- SHADER PARAM ---")
		print("Z/X: Adjust shader value for focused model (0..1)")
		print("V: Toggle logo mask post-process")
		print("B: Toggle decal visibility")
		print("ESC: Exit")
		print("=" * 64)

	def _init_audio(self):
		if not os.path.exists(self.music_path):
			print(f"[Audio] Music file not found: {self.music_path}")
			return

		try:
			if not pygame.mixer.get_init():
				pygame.mixer.init()
			pygame.mixer.music.load(self.music_path)
			pygame.mixer.music.set_volume(0.6)
			pygame.mixer.music.play(-1)
			print("[Audio] Background music playing.")
		except Exception as exc:
			print(f"[Audio] Could not start music: {exc}")

	def _shutdown_audio(self):
		if pygame.mixer.get_init():
			pygame.mixer.music.stop()
			pygame.mixer.quit()

	def _process_events(self):
		for event in pygame.event.get():
			if event.type == pygame.QUIT:
				self.running = False
			elif event.type == pygame.KEYDOWN:
				self._handle_keydown(event.key)
			elif event.type == pygame.MOUSEBUTTONDOWN:
				self._handle_mouse_button_down(event)
			elif event.type == pygame.MOUSEBUTTONUP:
				self._handle_mouse_button_up(event)
			elif event.type == pygame.MOUSEMOTION:
				self._handle_mouse_motion(event)

	def _handle_keydown(self, key):
		if key == pygame.K_ESCAPE:
			self.running = False
		elif key == pygame.K_m:
			model = self.scene.focus_previous(reset_angles=True)
			if model:
				print(f"Camera focus: {model.name}")
		elif key == pygame.K_n:
			model = self.scene.focus_next(reset_angles=True)
			if model:
				print(f"Camera focus: {model.name}")
		elif key == pygame.K_c:
			self.renderer.camera.ToggleCameraMode()
			mode = "Orbital" if self.renderer.camera.orbitMode else "Free"
			print(f"Camera Mode: {mode}")
		elif key == pygame.K_0:
			self._update_shader_for_focused(reset=True)
		elif key == pygame.K_1:
			self._update_shader_for_focused(fragment_key="checker")
		elif key == pygame.K_2:
			self._update_shader_for_focused(fragment_key="fresnel")
		elif key == pygame.K_3:
			self._update_shader_for_focused(fragment_key="scanlines")
		elif key == pygame.K_4:
			self._update_shader_for_focused(vertex_key="decal", fragment_key="decal")
		elif key == pygame.K_5:
			self._update_shader_for_focused(fragment_key="unlit")
		elif key == pygame.K_6:
			self._update_shader_for_focused(vertex_key="basic")
		elif key == pygame.K_7:
			self._update_shader_for_focused(vertex_key="twist")
		elif key == pygame.K_8:
			self._update_shader_for_focused(vertex_key="pulse")
		elif key == pygame.K_9:
			self._update_shader_for_focused(vertex_key="ripple")
		elif key == pygame.K_p:
			self._apply_shader_preset()
		elif key == pygame.K_b:
			self.renderer.ToggleDecal()
		elif key == pygame.K_v:
			self.renderer.ToggleMaskOverlay()

	def _handle_mouse_button_down(self, event):
		if event.button in (1, 3):
			self.mouse_pressed = True
			self.mouse_button = event.button
			self.last_mouse_pos = pygame.mouse.get_pos()
			pygame.mouse.set_visible(False)
		elif event.button == 4:
			self.renderer.camera.Zoom(-0.5)
		elif event.button == 5:
			self.renderer.camera.Zoom(0.5)

	def _handle_mouse_button_up(self, event):
		if event.button in (1, 3):
			self.mouse_pressed = False
			self.mouse_button = None
			pygame.mouse.set_visible(True)

	def _handle_mouse_motion(self, event):
		if not self.mouse_pressed:
			return

		current_pos = pygame.mouse.get_pos()
		delta_x = current_pos[0] - self.last_mouse_pos[0]
		delta_y = current_pos[1] - self.last_mouse_pos[1]

		if self.renderer.camera.orbitMode:
			self.renderer.camera.OrbitHorizontal(delta_x * self.mouse_sensitivity)
			self.renderer.camera.OrbitVertical(-delta_y * self.mouse_sensitivity)
		else:
			deg_per_pixel = self.mouse_sensitivity * (180.0 / 3.14159265)
			self.renderer.camera.rotation.y += -delta_x * deg_per_pixel
			self.renderer.camera.rotation.x += -delta_y * deg_per_pixel

		self.last_mouse_pos = current_pos

	def _update_camera(self):
		camera = self.renderer.camera
		if camera.orbitMode:
			orbit_speed = 1.5
			zoom_speed = 4.0
			vertical_speed = 1.5

			if self._key(pygame.K_LEFT):
				camera.OrbitHorizontal(orbit_speed * self.delta_time)
			if self._key(pygame.K_RIGHT):
				camera.OrbitHorizontal(-orbit_speed * self.delta_time)
			if self._key(pygame.K_UP):
				camera.OrbitVertical(vertical_speed * self.delta_time)
			if self._key(pygame.K_DOWN):
				camera.OrbitVertical(-vertical_speed * self.delta_time)
			if self._key(pygame.K_w):
				camera.OrbitVertical(vertical_speed * self.delta_time)
			if self._key(pygame.K_s):
				camera.OrbitVertical(-vertical_speed * self.delta_time)
			if self._key(pygame.K_a):
				camera.Zoom(-zoom_speed * self.delta_time)
			if self._key(pygame.K_d):
				camera.Zoom(zoom_speed * self.delta_time)
		else:
			move_speed = 1.3
			identity = glm.mat4(1)
			pitch_mat = glm.rotate(identity, glm.radians(camera.rotation.x), glm.vec3(1, 0, 0))
			yaw_mat = glm.rotate(identity, glm.radians(camera.rotation.y), glm.vec3(0, 1, 0))
			roll_mat = glm.rotate(identity, glm.radians(camera.rotation.z), glm.vec3(0, 0, 1))
			rotation_mat = pitch_mat * yaw_mat * roll_mat

			right = glm.normalize(glm.vec3(rotation_mat * glm.vec4(1, 0, 0, 0)))
			forward = glm.normalize(glm.vec3(rotation_mat * glm.vec4(0, 0, -1, 0)))

			if self._key(pygame.K_UP):
				camera.position += forward * (move_speed * self.delta_time)
			if self._key(pygame.K_DOWN):
				camera.position -= forward * (move_speed * self.delta_time)
			if self._key(pygame.K_RIGHT):
				camera.position += right * (move_speed * self.delta_time)
			if self._key(pygame.K_LEFT):
				camera.position -= right * (move_speed * self.delta_time)

			rot_speed = 35.0
			if self._key(pygame.K_w):
				camera.rotation.x += rot_speed * self.delta_time
			if self._key(pygame.K_s):
				camera.rotation.x -= rot_speed * self.delta_time
			if self._key(pygame.K_a):
				camera.rotation.y += rot_speed * self.delta_time
			if self._key(pygame.K_d):
				camera.rotation.y -= rot_speed * self.delta_time
			if self._key(pygame.K_q):
				camera.rotation.z += rot_speed * self.delta_time
			if self._key(pygame.K_e):
				camera.rotation.z -= rot_speed * self.delta_time

	def _update_lights(self):
		if self._key(pygame.K_t):
			self.renderer.pointLight.z -= 10 * self.delta_time
		if self._key(pygame.K_g):
			self.renderer.pointLight.z += 10 * self.delta_time
		if self._key(pygame.K_f):
			self.renderer.pointLight.x -= 10 * self.delta_time
		if self._key(pygame.K_h):
			self.renderer.pointLight.x += 10 * self.delta_time
		if self._key(pygame.K_r):
			self.renderer.pointLight.y -= 10 * self.delta_time
		if self._key(pygame.K_y):
			self.renderer.pointLight.y += 10 * self.delta_time

	def _update_shader_value(self):
		model = self.scene.get_focused_model()
		if not model:
			return

		current = getattr(model, "shaderValue", self.renderer.value)
		step = 1.0 * self.delta_time
		changed = False

		if self._key(pygame.K_z) and current > 0.0:
			current = max(0.0, current - step)
			changed = True
		if self._key(pygame.K_x) and current < 1.0:
			current = min(1.0, current + step)
			changed = True

		if changed:
			model.shaderValue = current

	def _key(self, key):
		return self.keys and self.keys[key]

	def _update_shader_for_focused(self, *, vertex_key=None, fragment_key=None, reset=False):
		model = self.scene.get_focused_model()
		if not model:
			return

		state = self.model_shader_state.setdefault(
			model,
			{"vertex": self.default_vertex_key, "fragment": self.default_fragment_key},
		)

		if reset:
			state["vertex"] = self.default_vertex_key
			state["fragment"] = self.default_fragment_key
		else:
			if vertex_key:
				new_vertex = (
					self.default_vertex_key
					if state["vertex"] == vertex_key
					else vertex_key
				)
				state["vertex"] = new_vertex
			if fragment_key:
				new_fragment = (
					self.default_fragment_key
					if state["fragment"] == fragment_key
					else fragment_key
				)
				state["fragment"] = new_fragment

		self._apply_shader_to_model(
			model,
			state["vertex"],
			state["fragment"],
			announce=True,
		)

	def _load_sample_models(self):
		self._build_scene()

	def _apply_shader_to_model(self, model, vertex_key, fragment_key, *, announce=False):
		if model is None:
			return False

		state = self.model_shader_state.setdefault(
			model,
			{"vertex": self.default_vertex_key, "fragment": self.default_fragment_key},
		)
		state["vertex"] = vertex_key
		state["fragment"] = fragment_key

		vertex_src = self.vertex_shaders[vertex_key]
		fragment_src = self.fragment_shaders[fragment_key]
		self.scene.set_model_shaders(model, vertex_src, fragment_src)
		model.shaderValue = getattr(model, "shaderValue", 0.0)

		if vertex_key == "decal" or fragment_key == "decal":
			self.renderer.ConfigureDecalForModel(model)

		self._update_decal_global_state()

		if announce:
			print(f"Shaders for {model.name}: {vertex_key} + {fragment_key}")
			if self.preset_active:
				self.preset_active = False
		return True

	def _update_decal_global_state(self):
		self.renderer.decalEnabled = any(
			entry_state["vertex"] == "decal" or entry_state["fragment"] == "decal"
			for entry_state in self.model_shader_state.values()
		)

	def _find_model_by_name(self, name):
		for entry in self.scene.get_models():
			if entry.name == name:
				return entry
		return None

	def _apply_shader_preset(self):
		if self.preset_active:
			self._reset_all_shaders_to_default()
			return

		baseline_value = self.shader_baseline_value
		preset = [
			("TASM 2", "ripple", "unlit", 0.01),
			("Spiderman 3", "pulse", "checker", 0.1),
			("Wood Box (Stacked)", "decal", "decal", baseline_value),
			("Wood Box", "decal", "decal", baseline_value),
			("Camioneta", "twist", "fresnel", 0.15),
		]

		applied = []
		missing = []
		for name, vertex_key, fragment_key, value in preset:
			model = self._find_model_by_name(name)
			if model is None:
				missing.append(name)
				continue
			self._apply_shader_to_model(model, vertex_key, fragment_key, announce=False)
			model.shaderValue = float(value)
			applied.append((model, name, vertex_key, fragment_key, value))

		preset_models = {entry[0] for entry in applied}
		for model in self.scene.get_models():
			if model not in preset_models:
				model.shaderValue = baseline_value
				self._apply_shader_to_model(model, self.default_vertex_key, self.default_fragment_key, announce=False)

		if applied:
			print("[Preset] Applied shader configuration:")
			for _, name, vertex_key, fragment_key, value in applied:
				print(f"  - {name}: {vertex_key} + {fragment_key} (value={value:.2f})")
		else:
			print("[Preset] No models were updated (not found).")

		if missing:
			print("[Preset] Missing models:", ", ".join(missing))

		self.preset_active = bool(applied)

	def _reset_all_shaders_to_default(self):
		for model in self.scene.get_models():
			self._apply_shader_to_model(
				model,
				self.default_vertex_key,
				self.default_fragment_key,
				announce=False,
			)
			model.shaderValue = self.shader_baseline_value

		self.preset_active = False
		self._update_decal_global_state()
		print("[Preset] Scene reset to default shaders.")

	def _build_scene(self):
		tile_size = 2.0
		columns = 6
		rows = 5
		grid_center = glm.vec3(0.0, 0.0, -6.0)

		def grid_position(column, row):
			col = float(column)
			row = float(row)
			x = (col - ((columns + 1) / 2.0)) * tile_size
			z = (row - ((rows + 1) / 2.0)) * tile_size
			return glm.vec3(grid_center.x + x, 0.0, grid_center.z + z)

		def apply_transform(model, location, scale_vec):
			model.scale = scale_vec
			min_corner = model.sourceBoundsMin
			center = model.sourceBoundsCenter
			model.position = glm.vec3(
				location.x - center.x * scale_vec.x,
				location.y - min_corner.y * scale_vec.y,
				location.z - center.z * scale_vec.z,
			)

		# Floor covering the entire grid
		try:
			floor = Model("models/Floor/floor.obj", name="Floor")
		except FileNotFoundError as exc:
			print(f"[Scene] Could not load floor OBJ: {exc}")
			floor = None
		else:
			floor_scale = glm.vec3(
				(tile_size * columns) / max(floor.sourceBoundsSize.x, 1e-4) + 1,
				1.0,
				(tile_size * rows) / max(floor.sourceBoundsSize.z, 1e-4),
			)
			floor.scale = floor_scale
			floor.position = glm.vec3(
				grid_center.x - floor.sourceBoundsCenter.x * floor_scale.x,
				-floor.sourceBoundsMax.y * floor_scale.y,
				grid_center.z - floor.sourceBoundsCenter.z * floor_scale.z,
			)
			floor.position.y -= 0.01  # slight sink to avoid z-fighting
			self.renderer.scene.append(floor)

		# Back wall spanning four tiles (columns 3-6, row 1)
		try:
			wall = Model("models/Wall/wall.obj", name="Back Wall")
		except FileNotFoundError as exc:
			print(f"[Scene] Could not load wall OBJ: {exc}")
		else:
			wall_scale = glm.vec3(
				(tile_size * 4.0 + 0.5) / max(wall.sourceBoundsSize.x, 1e-4),
				1.0,
				1.0,
			)
			apply_transform(wall, grid_position(6.0, 1.0), wall_scale)
			self.renderer.scene.append(wall)

		# Camioneta on row 2, column 2
		try:
			camioneta = Model("models/Camioneta/camioneta_Low.obj", name="Camioneta")
		except FileNotFoundError as exc:
			print(f"[Scene] Could not load Camioneta OBJ: {exc}")
		else:
			target_length = tile_size * 2.5
			scale_value = target_length / max(camioneta.sourceBoundsSize.x, 1e-4) * 0.70
			camioneta_scale = glm.vec3(scale_value, scale_value, scale_value)
			apply_transform(camioneta, grid_position(1.5, 2.0), camioneta_scale)
			camioneta.rotation.y = 295.0
			scaled_radius = camioneta.GetScaledRadius()
			focus_distance = max(6.0, float(scaled_radius) * 2.5)
			self._register_model(
				camioneta,
				vertex_key="basic",
				fragment_key="basic",
				focus_distance=focus_distance,
				reset_camera=False,
			)

		# Wood box at grid (4,2)
		try:
			wood_box = Model("models/Wood Box/wood_box.obj", name="Wood Box")
		except FileNotFoundError as exc:
			print(f"[Scene] Could not load Wood Box OBJ: {exc}")
		else:
			# Scale so its X footprint matches one tile
			box_scale_val = tile_size / max(wood_box.sourceBoundsSize.x, 1e-4) * .66
			box_scale = glm.vec3(box_scale_val, box_scale_val, box_scale_val)
			apply_transform(wood_box, grid_position(5.5, 2.0), box_scale)
			wood_box.rotation.y = 25.0
			box_height = wood_box.sourceBoundsSize.y * box_scale.y
			box_radius = wood_box.GetScaledRadius()
			focus_distance = max(4.0, float(box_radius) * 3.0)
			self._register_model(
				wood_box,
				vertex_key="basic",
				fragment_key="basic",
				focus_distance=focus_distance,
				reset_camera=False,
			)

			# Stack a second crate slightly offset above the first.
			try:
				stacked_box = Model("models/Wood Box/wood_box.obj", name="Wood Box (Stacked)")
			except FileNotFoundError as exc:
				print(f"[Scene] Could not load stacked Wood Box OBJ: {exc}")
			else:
				apply_transform(stacked_box, grid_position(5.5, 2.0), box_scale)
				stacked_box.rotation.y = 40.0
				stack_offset = glm.vec3(box_scale.x * 0.35, box_height, -box_scale.z * 0.25)
				stacked_box.position += stack_offset
				stacked_radius = stacked_box.GetScaledRadius()
				stacked_focus_distance = max(4.0, float(stacked_radius) * 3.0)
				self._register_model(
					stacked_box,
					vertex_key="basic",
					fragment_key="basic",
					focus_distance=stacked_focus_distance,
					reset_camera=False,
				)

		# Spiderman 3 on the right, looking towards TASM 2
		try:
			spiderman = Model(
				"models/Spiderman/Spiderman 3/out/HOMECOMING SUIT.obj",
				name="Spiderman 3",
			)
		except FileNotFoundError as exc:
			print(f"[Scene] Could not load Spiderman 3 OBJ: {exc}")
		else:
			target_height = 2.4
			scale_value = target_height / max(spiderman.sourceBoundsSize.y, 1e-4)
			spiderman_scale = glm.vec3(scale_value, scale_value, scale_value)
			apply_transform(spiderman, grid_position(5.0, 3.0), spiderman_scale)
			spiderman.rotation.y = -90.0
			scaled_radius = spiderman.GetScaledRadius()
			focus_distance = max(4.5, float(scaled_radius) * 2.5)
			self._set_model_focus_point(spiderman, height_ratio=0.68)
			self._register_model(
				spiderman,
				vertex_key="basic",
				fragment_key="basic",
				focus_distance=focus_distance,
				reset_camera=True,
			)

		# TASM 2 at the center, facing Spiderman 3
		try:
			tasm2 = Model("models/Spiderman/TASM 2/other format/TASM 2.obj", name="TASM 2")
		except FileNotFoundError as exc:
			print(f"[Scene] Could not load TASM 2 OBJ: {exc}")
		else:
			target_height = 2.5
			scale_value = target_height / max(tasm2.sourceBoundsSize.y, 1e-4)
			tasm_scale = glm.vec3(scale_value, scale_value, scale_value)
			apply_transform(tasm2, grid_position(3.0, 3.0), tasm_scale)
			tasm2.rotation.y = 90.0
			scaled_radius = tasm2.GetScaledRadius()
			focus_distance = max(4.5, float(scaled_radius) * 2.5)
			self._set_model_focus_point(tasm2, height_ratio=0.68)
			self._register_model(
				tasm2,
				vertex_key="basic",
				fragment_key="basic",
				focus_distance=focus_distance,
				reset_camera=False,
			)

	def _load_tasm2_sample(self):
		model_path = "models/Spiderman/TASM 2/other format/TASM 2.obj"
		try:
			model = Model(model_path, name="TASM 2")
		except FileNotFoundError as exc:
			print(f"[Sample] Could not load TASM 2 OBJ: {exc}")
			return

		target_height = 2.4
		source_height = max(model.sourceBoundsSize.y, 1e-4)
		scale_factor = target_height / source_height
		model.scale = glm.vec3(scale_factor, scale_factor, scale_factor)

		center = model.sourceBoundsCenter
		min_corner = model.sourceBoundsMin

		model.position = glm.vec3(
			-center.x * scale_factor,
			-min_corner.y * scale_factor,
			-center.z * scale_factor - 6.0,
		)

		scaled_radius = model.GetScaledRadius()
		focus_distance = max(4.5, float(scaled_radius) * 2.5)
		self._set_model_focus_point(model, height_ratio=0.68)

		self._register_model(
			model,
			vertex_key="basic",
			fragment_key="basic",
			focus_distance=focus_distance,
			reset_camera=True,
		)

	def _load_spiderman_sample(self):
		model_path = "models/Spiderman/Spiderman 3/out/HOMECOMING SUIT.obj"
		try:
			model = Model(model_path, name="HOMECOMING SUIT")
		except FileNotFoundError as exc:
			print(f"[Sample] Could not load Spiderman OBJ: {exc}")
			return

		target_height = 2.4
		source_height = max(model.sourceBoundsSize.y, 1e-4)
		scale_factor = target_height / source_height
		model.scale = glm.vec3(scale_factor, scale_factor, scale_factor)

		center = model.sourceBoundsCenter
		min_corner = model.sourceBoundsMin

		model.position = glm.vec3(
			-center.x * scale_factor,
			-min_corner.y * scale_factor,
			-center.z * scale_factor - 6.0,
		)

		scaled_radius = model.GetScaledRadius()
		focus_distance = max(4.5, float(scaled_radius) * 2.5)
		self._set_model_focus_point(model, height_ratio=0.68)

		self._register_model(
			model,
			vertex_key="basic",
			fragment_key="basic",
			focus_distance=focus_distance,
			reset_camera=True,
		)

	def _register_model(self, model, *, vertex_key=None, fragment_key=None, focus_distance=None, reset_camera=False):
		vertex_key = vertex_key or self.default_vertex_key
		fragment_key = fragment_key or self.default_fragment_key
		shader_pair = (self.vertex_shaders[vertex_key], self.fragment_shaders[fragment_key])
		self.scene.add_model(
			model,
			shader_pair=shader_pair,
			focus_distance=focus_distance,
			reset_camera=reset_camera,
		)
		self.model_shader_state[model] = {"vertex": vertex_key, "fragment": fragment_key}

		if focus_distance is not None:
			model.cameraFocusDistance = focus_distance

	def _set_model_focus_point(self, model, *, height_ratio=0.6, height_offset=0.0):
		height_ratio = max(0.0, min(1.0, float(height_ratio)))
		scale = model.scale
		center = model.sourceBoundsCenter
		min_corner = model.sourceBoundsMin
		size = model.sourceBoundsSize

		world_center_x = model.position.x + center.x * scale.x
		world_center_z = model.position.z + center.z * scale.z

		world_min_y = model.position.y + min_corner.y * scale.y
		world_height = size.y * scale.y
		focus_y = world_min_y + world_height * height_ratio + height_offset

		model.cameraFocusPoint = glm.vec3(world_center_x, focus_y, world_center_z)


if __name__ == "__main__":
	app = DioramaApp(WIDTH, HEIGHT)
	app.run()