import ctypes

import glm # pip install PyGLM
import numpy as np
import pygame
from OpenGL.GL import *
from OpenGL.GL.shaders import compileProgram, compileShader

from camera import Camera
from skybox import Skybox
from vertexShaders import screen_quad_vertex_shader
from fragmentShaders import mask_vignette_fragment_shader

class Renderer(object):
    def __init__(self, screen):
        self.screen = screen
        _,_, self.width, self.height = screen.get_rect()
        
        glClearColor(0.2, 0.2, 0.2, 1.0)

        glEnable(GL_DEPTH_TEST)
        glViewport(0,0, self.width, self.height)

        self.camera = Camera(self.width, self.height)

        self.scene = []
        

        self.filledMode = False
        self.ToggleFilledMode()

        self.activeShader = None
        self.defaultVertexShaderSource = None
        self.defaultFragmentShaderSource = None
        self._shaderCache = {}
        self._lastUsedProgram = None

        self.skybox = None

        self.pointLight = glm.vec3(0,0,0)
        self.ambientLight = 0.1


        self.value = 0.0;
        self.elapsedTime = 0.0;

        self.postprocessEnabled = False
        self.maskBlend = 1.0
        self.maskFeather = 0.08
        self.exteriorColor = glm.vec3(0.0, 0.0, 0.0)
        self.maskInvert = False
        self.maskTexturePath = "assets/Logo.png"

        self._sceneFBO = None
        self._sceneColorTex = None
        self._sceneDepthRBO = None
        self._quadVAO = None
        self._quadVBO = None
        self._postprocessProgram = None
        self._maskTexture = None
        self._maskTextureSize = (1, 1)
        self._maskScale = glm.vec2(1.0, 1.0)

        self.decalEnabled = False
        self.decalStrength = 1.0
        self.decalDepth = 0.05
        self.decalCenter = glm.vec3(0.0, 0.0, 0.0)
        self.decalNormal = glm.vec3(0.0, 0.0, 1.0)
        self.decalUp = glm.vec3(0.0, 1.0, 0.0)
        self.decalSize = glm.vec2(1.0, 1.0)
        self.decalTexturePath = "assets/Mask.png"
        self._decalTexture = None

        self._normalize_decal_axes()
        self._init_postprocess_resources()
        self.LoadDecalTexture(self.decalTexturePath)



    def CreateSkybox(self, textureList):
        self.skybox = Skybox(textureList)
        self.skybox.cameraRef = self.camera


    def ToggleFilledMode(self):
        self.filledMode = not self.filledMode

        if self.filledMode:
            glEnable(GL_CULL_FACE)
            glPolygonMode(GL_FRONT, GL_FILL)
        else:
            glDisable(GL_CULL_FACE)
            glPolygonMode(GL_FRONT_AND_BACK, GL_LINE)


    def SetShaders(self, vertexShader, fragmentShader):
        self.defaultVertexShaderSource = vertexShader
        self.defaultFragmentShaderSource = fragmentShader

        if vertexShader is None or fragmentShader is None:
            self.activeShader = None
            return

        self.activeShader = self._compile_shader_program(vertexShader, fragmentShader)


    def SetModelShaders(self, model, vertexShader, fragmentShader):
        if model is None:
            raise ValueError("Model reference is required to assign shaders")

        program = self._compile_shader_program(vertexShader, fragmentShader)
        model.SetShaderProgram(program)
        return program


    def ClearModelShaders(self, model):
        if model is None:
            return
        model.SetShaderProgram(None)


    def FocusOnModel(self, model, *, distance=None, reset_angles=False):
        if model is None:
            return

        focus_point = getattr(model, "cameraFocusPoint", None)
        if focus_point is None:
            focus_point = model.GetFocusPoint() if hasattr(model, "GetFocusPoint") else model.position
        target_distance = distance if distance is not None else getattr(model, "cameraFocusDistance", None)
        self.camera.FocusOn(focus_point, distance=target_distance, reset_angles=reset_angles)


    def Render(self):
        self._refresh_backbuffer_dimensions()

        use_postprocess = self.postprocessEnabled and self._postprocess_available()

        if use_postprocess:
            self._bind_scene_fbo()
            self._draw_scene_contents()
            self._composite_postprocess()
        else:
            self._bind_default_framebuffer()
            self._draw_scene_contents()


    def ToggleMaskOverlay(self):
        if not self._postprocess_available():
            self._init_postprocess_resources()

        if not self._postprocess_available():
            print("[PostProcess] Mask overlay unavailable (missing resources).")
            self.postprocessEnabled = False
            return

        self.postprocessEnabled = not self.postprocessEnabled
        state = "ON" if self.postprocessEnabled else "OFF"
        print(f"[PostProcess] Logo mask {state}.")


    def ToggleDecal(self):
        self.decalEnabled = not self.decalEnabled
        state = "ON" if self.decalEnabled else "OFF"
        print(f"[Decal] Model decal {state}.")


    def LoadMaskTexture(self, path):
        self.maskTexturePath = path or ""
        self._load_mask_texture(self.maskTexturePath)
        self._compute_mask_scale()
        if self._maskTexture:
            print(f"[PostProcess] Mask texture loaded: {self.maskTexturePath}")
        else:
            print(f"[PostProcess] Failed to load mask texture: {self.maskTexturePath}")


    def LoadDecalTexture(self, path):
        self.decalTexturePath = path or ""
        if self._decalTexture:
            glDeleteTextures(1, [self._decalTexture])
            self._decalTexture = None

        texture, _ = self._load_rgba_texture(self.decalTexturePath, label="Decal")
        self._decalTexture = texture
        if self._decalTexture:
            print(f"[Decal] Texture loaded: {self.decalTexturePath}")
            self._bind_decal_texture()
        else:
            print(f"[Decal] Failed to load texture: {self.decalTexturePath}")


    def SetDecalParameters(
        self,
        *,
        center=None,
        normal=None,
        up=None,
        size=None,
        depth=None,
        strength=None,
    ):
        if center is not None:
            self.decalCenter = glm.vec3(center)
        if normal is not None:
            self.decalNormal = glm.vec3(normal)
        if up is not None:
            self.decalUp = glm.vec3(up)
        if size is not None:
            self.decalSize = glm.vec2(size)
        if depth is not None:
            self.decalDepth = max(float(depth), 1e-4)
        if strength is not None:
            self.decalStrength = float(strength)
        self._normalize_decal_axes()


    def ConfigureDecalForModel(self, model, *, coverage=0.6, depth_factor=0.2):
        if model is None:
            return

        center = glm.vec3(model.sourceBoundsCenter.x, model.sourceBoundsCenter.y, model.sourceBoundsCenter.z)

        size_x = max(model.sourceBoundsSize.x * coverage, 1e-4)
        size_y = max(model.sourceBoundsSize.y * coverage, 1e-4)

        depth = max(model.sourceBoundsSize.z * depth_factor, 1e-4)
        center.z = model.sourceBoundsMax.z - depth * 0.5

        self.decalCenter = center
        self.decalSize = glm.vec2(size_x, size_y)
        self.decalDepth = depth
        self.decalNormal = glm.vec3(0.0, 0.0, 1.0)
        self.decalUp = glm.vec3(0.0, 1.0, 0.0)
        self.decalEnabled = True
        self._normalize_decal_axes()


    def _refresh_backbuffer_dimensions(self):
        _, _, width, height = self.screen.get_rect()
        if width == self.width and height == self.height:
            return

        self.width = width
        self.height = height
        glViewport(0, 0, self.width, self.height)
        self.camera.screenWidth = self.width
        self.camera.screenHeight = self.height
        self.camera.CreateProjectionMatrix(60, 0.1, 1000)
        self._init_postprocess_resources()


    def _bind_scene_fbo(self):
        glBindFramebuffer(GL_FRAMEBUFFER, self._sceneFBO or 0)
        glViewport(0, 0, self.width, self.height)


    def _bind_default_framebuffer(self):
        glBindFramebuffer(GL_FRAMEBUFFER, 0)
        glViewport(0, 0, self.width, self.height)


    def _draw_scene_contents(self):
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        self.camera.Update()

        if self.skybox is not None:
            self.skybox.Render()
        self._lastUsedProgram = None

        for obj in self.scene:
            program = getattr(obj, "shaderProgram", None) or self.activeShader
            if program is None:
                continue

            if program != self._lastUsedProgram:
                glUseProgram(program)
                self._apply_common_uniforms(program)
                self._lastUsedProgram = program
                self._bind_decal_texture()

            location = glGetUniformLocation(program, "modelMatrix")
            if location != -1:
                glUniformMatrix4fv(location, 1, GL_FALSE, glm.value_ptr(obj.GetModelMatrix()))

            shader_value = getattr(obj, "shaderValue", self.value)
            self._set_uniform_float(program, "value", shader_value)

            obj.Render()


    def _composite_postprocess(self):
        glBindFramebuffer(GL_FRAMEBUFFER, 0)
        glViewport(0, 0, self.width, self.height)

        glDisable(GL_DEPTH_TEST)
        glClear(GL_COLOR_BUFFER_BIT)

        if self._postprocessProgram is None:
            return

        glUseProgram(self._postprocessProgram)

        glActiveTexture(GL_TEXTURE0)
        glBindTexture(GL_TEXTURE_2D, self._sceneColorTex or 0)
        glActiveTexture(GL_TEXTURE1)
        glBindTexture(GL_TEXTURE_2D, self._maskTexture or 0)

        blend = self.maskBlend if self.postprocessEnabled else 0.0
        invert_value = 1.0 if self.maskInvert else 0.0
        scale_x, scale_y = self._maskScale

        self._set_uniform_float(self._postprocessProgram, "blend", blend)
        self._set_uniform_float(self._postprocessProgram, "smoothness", self.maskFeather)
        self._set_uniform_float(self._postprocessProgram, "invertMask", invert_value)
        self._set_uniform_vec2(self._postprocessProgram, "maskScale", scale_x, scale_y)
        self._set_uniform_vec3(self._postprocessProgram, "exteriorColor", self.exteriorColor)

        glBindVertexArray(self._quadVAO or 0)
        glDrawArrays(GL_TRIANGLES, 0, 6)
        glBindVertexArray(0)

        glBindTexture(GL_TEXTURE_2D, 0)
        glActiveTexture(GL_TEXTURE0)
        glUseProgram(0)
        glEnable(GL_DEPTH_TEST)


    def _postprocess_available(self):
        return all([
            self._sceneFBO,
            self._sceneColorTex,
            self._quadVAO,
            self._postprocessProgram,
            self._maskTexture,
        ])


    def _init_postprocess_resources(self):
        self._create_scene_targets()
        self._create_screen_quad()
        self._compile_postprocess_shader()
        self._load_mask_texture(self.maskTexturePath)
        self._compute_mask_scale()


    def _create_scene_targets(self):
        if self.width <= 0 or self.height <= 0:
            return

        if self._sceneFBO:
            glDeleteFramebuffers(1, [self._sceneFBO])
            self._sceneFBO = None
        if self._sceneColorTex:
            glDeleteTextures(1, [self._sceneColorTex])
            self._sceneColorTex = None
        if self._sceneDepthRBO:
            glDeleteRenderbuffers(1, [self._sceneDepthRBO])
            self._sceneDepthRBO = None

        self._sceneFBO = glGenFramebuffers(1)
        glBindFramebuffer(GL_FRAMEBUFFER, self._sceneFBO)

        self._sceneColorTex = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, self._sceneColorTex)
        glTexImage2D(
            GL_TEXTURE_2D,
            0,
            GL_RGB8,
            self.width,
            self.height,
            0,
            GL_RGB,
            GL_UNSIGNED_BYTE,
            None,
        )
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)

        self._sceneDepthRBO = glGenRenderbuffers(1)
        glBindRenderbuffer(GL_RENDERBUFFER, self._sceneDepthRBO)
        glRenderbufferStorage(GL_RENDERBUFFER, GL_DEPTH24_STENCIL8, self.width, self.height)
        glFramebufferRenderbuffer(GL_FRAMEBUFFER, GL_DEPTH_STENCIL_ATTACHMENT, GL_RENDERBUFFER, self._sceneDepthRBO)

        glFramebufferTexture2D(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_TEXTURE_2D, self._sceneColorTex, 0)

        status = glCheckFramebufferStatus(GL_FRAMEBUFFER)
        if status != GL_FRAMEBUFFER_COMPLETE:
            print(f"[PostProcess] Framebuffer incomplete: {status}")

        glBindFramebuffer(GL_FRAMEBUFFER, 0)
        glBindTexture(GL_TEXTURE_2D, 0)
        glBindRenderbuffer(GL_RENDERBUFFER, 0)


    def _create_screen_quad(self):
        if self._quadVAO and self._quadVBO:
            return

        vertices = np.array([
            -1.0, -1.0, 0.0, 0.0,
             1.0, -1.0, 1.0, 0.0,
             1.0,  1.0, 1.0, 1.0,
            -1.0, -1.0, 0.0, 0.0,
             1.0,  1.0, 1.0, 1.0,
            -1.0,  1.0, 0.0, 1.0,
        ], dtype=np.float32)

        self._quadVAO = glGenVertexArrays(1)
        self._quadVBO = glGenBuffers(1)

        glBindVertexArray(self._quadVAO)
        glBindBuffer(GL_ARRAY_BUFFER, self._quadVBO)
        glBufferData(GL_ARRAY_BUFFER, vertices.nbytes, vertices, GL_STATIC_DRAW)

        stride = 4 * vertices.itemsize
        glEnableVertexAttribArray(0)
        glVertexAttribPointer(0, 2, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(0))
        glEnableVertexAttribArray(1)
        glVertexAttribPointer(1, 2, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(2 * vertices.itemsize))

        glBindBuffer(GL_ARRAY_BUFFER, 0)
        glBindVertexArray(0)


    def _compile_postprocess_shader(self):
        if self._postprocessProgram:
            return

        try:
            program = compileProgram(
                compileShader(screen_quad_vertex_shader, GL_VERTEX_SHADER),
                compileShader(mask_vignette_fragment_shader, GL_FRAGMENT_SHADER),
            )
        except Exception as exc:
            print(f"[PostProcess] Failed to compile post-process shader: {exc}")
            self._postprocessProgram = None
            return

        self._postprocessProgram = program
        glUseProgram(self._postprocessProgram)
        glUniform1i(glGetUniformLocation(self._postprocessProgram, "sceneTex"), 0)
        glUniform1i(glGetUniformLocation(self._postprocessProgram, "maskTex"), 1)
        glUseProgram(0)


    def _load_mask_texture(self, path):
        if not path:
            self._maskTexture = None
            return

        texture, size = self._load_rgba_texture(path, label="PostProcess")
        if self._maskTexture:
            glDeleteTextures(1, [self._maskTexture])
        self._maskTexture = texture
        self._maskTextureSize = size if size else (1, 1)


    def _compute_mask_scale(self):
        width, height = self._maskTextureSize
        if self.height == 0 or height == 0:
            self._maskScale = (1.0, 1.0)
            return

        screen_aspect = float(self.width) / float(self.height)
        mask_aspect = float(width) / float(height) if height else 1.0

        scale_x = 1.0
        scale_y = 1.0

        if screen_aspect >= mask_aspect:
            scale_x = screen_aspect / mask_aspect
        else:
            scale_y = mask_aspect / screen_aspect

        self._maskScale = (scale_x, scale_y)


    def _load_rgba_texture(self, path, label="Texture"):
        if not path:
            return None, (0, 0)

        try:
            surface = pygame.image.load(path).convert_alpha()
        except Exception as exc:
            print(f"[{label}] Could not load texture '{path}': {exc}")
            return None, (0, 0)

        texture = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, texture)
        texture_data = pygame.image.tostring(surface, "RGBA", True)
        glTexImage2D(
            GL_TEXTURE_2D,
            0,
            GL_RGBA,
            surface.get_width(),
            surface.get_height(),
            0,
            GL_RGBA,
            GL_UNSIGNED_BYTE,
            texture_data,
        )
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
        glBindTexture(GL_TEXTURE_2D, 0)

        return texture, (surface.get_width(), surface.get_height())


    def _normalize_decal_axes(self):
        if glm.length(self.decalNormal) < 1e-5:
            self.decalNormal = glm.vec3(0.0, 0.0, 1.0)
        if glm.length(self.decalUp) < 1e-5:
            self.decalUp = glm.vec3(0.0, 1.0, 0.0)

        n = glm.normalize(self.decalNormal)
        u = self.decalUp - n * glm.dot(self.decalUp, n)
        if glm.length(u) < 1e-5:
            fallback = glm.vec3(0.0, 1.0, 0.0)
            if abs(glm.dot(fallback, n)) > 0.95:
                fallback = glm.vec3(1.0, 0.0, 0.0)
            u = fallback - n * glm.dot(fallback, n)
        u = glm.normalize(u)
        self.decalNormal = n
        self.decalUp = u


    def _compile_shader_program(self, vertexShader, fragmentShader):
        key = (vertexShader, fragmentShader)
        program = self._shaderCache.get(key)
        if program is not None:
            return program

        program = compileProgram(
            compileShader(vertexShader, GL_VERTEX_SHADER),
            compileShader(fragmentShader, GL_FRAGMENT_SHADER)
        )
        self._shaderCache[key] = program
        return program


    def _apply_common_uniforms(self, program):
        self._set_uniform_mat4(program, "viewMatrix", self.camera.viewMatrix)
        self._set_uniform_mat4(program, "projectionMatrix", self.camera.projectionMatrix)

        self._set_uniform_vec3(program, "pointLight", self.pointLight)
        self._set_uniform_float(program, "ambientLight", self.ambientLight)

        self._set_uniform_float(program, "time", self.elapsedTime)
        self._set_uniform_vec3(program, "cameraPos", self.camera.position)

        self._set_uniform_int(program, "tex0", 0)
        self._set_uniform_int(program, "tex1", 1)

        self._set_uniform_int(program, "decalEnabled", 1 if self.decalEnabled else 0)
        self._set_uniform_float(program, "decalStrength", self.decalStrength)
        self._set_uniform_float(program, "decalDepth", self.decalDepth)
        self._set_uniform_vec3(program, "decalCenter", self.decalCenter)
        self._set_uniform_vec3(program, "decalNormal", self.decalNormal)
        self._set_uniform_vec3(program, "decalUp", self.decalUp)
        self._set_uniform_vec2(program, "decalSize", float(self.decalSize.x), float(self.decalSize.y))


    def _set_uniform_mat4(self, program, name, matrix):
        location = glGetUniformLocation(program, name)
        if location != -1:
            glUniformMatrix4fv(location, 1, GL_FALSE, glm.value_ptr(matrix))


    def _set_uniform_vec2(self, program, name, x, y):
        location = glGetUniformLocation(program, name)
        if location != -1:
            glUniform2f(location, x, y)


    def _set_uniform_vec3(self, program, name, value):
        location = glGetUniformLocation(program, name)
        if location != -1:
            glUniform3fv(location, 1, glm.value_ptr(value))


    def _set_uniform_float(self, program, name, value):
        location = glGetUniformLocation(program, name)
        if location != -1:
            glUniform1f(location, value)


    def _set_uniform_int(self, program, name, value):
        location = glGetUniformLocation(program, name)
        if location != -1:
            glUniform1i(location, value)


    def _bind_decal_texture(self):
        glActiveTexture(GL_TEXTURE1)
        glBindTexture(GL_TEXTURE_2D, self._decalTexture or 0)
        glActiveTexture(GL_TEXTURE0)

