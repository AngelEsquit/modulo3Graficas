
from numpy import array, float32
import glm
from OpenGL.GL import * 
from OpenGL.GL.shaders import compileProgram, compileShader
import pygame


VERTEX_SHADER_CODE = '''
#version 450 core

layout (location = 0) in vec3 inPosition;

uniform mat4 viewMatrix;
uniform mat4 projectionMatrix;


out vec3 texCoords;

void main()
{
    texCoords = inPosition;
    mat4 vm = mat4(mat3(viewMatrix));
    gl_Position = projectionMatrix * vm * vec4(inPosition, 1.0);
}

'''


FRAGMENT_SHADER_CODE = '''
#version 450 core

uniform samplerCube skybox;

in vec3 texCoords;

out vec4 fragColor;

void main()
{
    fragColor = texture(skybox, texCoords);
}

'''


class Skybox(object):
	def __init__(self, textureList):
		self.cameraRef = None
		self._texturePaths = textureList
		self._vertexCount = 36
		
		# Inicialización en cascada
		self._initializeGeometry()
		self._compileShaderProgram()
		self._setupCubemapTexture()
		

	def _initializeGeometry(self):
		"""Crea y configura la geometría del cubo del skybox"""
		cubeVertices = self._generateCubeVertices()
		self.vertexBuffer = array(cubeVertices, dtype=float32)
		self.VBO = glGenBuffers(1)
		
	
	def _generateCubeVertices(self):
		"""Genera los vértices para las 6 caras del cubo"""
		return [
			# Cara frontal (Z negativo)
			-1.0,  1.0, -1.0,  -1.0, -1.0, -1.0,   1.0, -1.0, -1.0,
			 1.0, -1.0, -1.0,   1.0,  1.0, -1.0,  -1.0,  1.0, -1.0,
			
			# Cara izquierda (X negativo)
			-1.0, -1.0,  1.0,  -1.0, -1.0, -1.0,  -1.0,  1.0, -1.0,
			-1.0,  1.0, -1.0,  -1.0,  1.0,  1.0,  -1.0, -1.0,  1.0,
			
			# Cara derecha (X positivo)
			 1.0, -1.0, -1.0,   1.0, -1.0,  1.0,   1.0,  1.0,  1.0,
			 1.0,  1.0,  1.0,   1.0,  1.0, -1.0,   1.0, -1.0, -1.0,
			
			# Cara trasera (Z positivo)
			-1.0, -1.0,  1.0,  -1.0,  1.0,  1.0,   1.0,  1.0,  1.0,
			 1.0,  1.0,  1.0,   1.0, -1.0,  1.0,  -1.0, -1.0,  1.0,
			
			# Cara superior (Y positivo)
			-1.0,  1.0, -1.0,   1.0,  1.0, -1.0,   1.0,  1.0,  1.0,
			 1.0,  1.0,  1.0,  -1.0,  1.0,  1.0,  -1.0,  1.0, -1.0,
			
			# Cara inferior (Y negativo)
			-1.0, -1.0, -1.0,  -1.0, -1.0,  1.0,   1.0, -1.0, -1.0,
			 1.0, -1.0, -1.0,  -1.0, -1.0,  1.0,   1.0, -1.0,  1.0
		]
	
	
	def _compileShaderProgram(self):
		"""Compila los shaders de vértice y fragmento"""
		vertexShader = compileShader(VERTEX_SHADER_CODE, GL_VERTEX_SHADER)
		fragmentShader = compileShader(FRAGMENT_SHADER_CODE, GL_FRAGMENT_SHADER)
		self.shaders = compileProgram(vertexShader, fragmentShader)
	
	
	def _setupCubemapTexture(self):
		"""Configura y carga el cubemap desde las imágenes proporcionadas"""
		self.texture = glGenTextures(1)
		glBindTexture(GL_TEXTURE_CUBE_MAP, self.texture)
		
		self._loadCubemapFaces()
		self._configureCubemapParameters()
		
	
	def _loadCubemapFaces(self):
		"""Carga cada cara del cubemap desde las texturas"""
		cubemapTargets = [
			GL_TEXTURE_CUBE_MAP_POSITIVE_X,
			GL_TEXTURE_CUBE_MAP_NEGATIVE_X,
			GL_TEXTURE_CUBE_MAP_POSITIVE_Y,
			GL_TEXTURE_CUBE_MAP_NEGATIVE_Y,
			GL_TEXTURE_CUBE_MAP_POSITIVE_Z,
			GL_TEXTURE_CUBE_MAP_NEGATIVE_Z
		]
		
		for faceIndex, texturePath in enumerate(self._texturePaths):
			self._loadTextureFace(cubemapTargets[faceIndex], texturePath)
	
	
	def _loadTextureFace(self, target, imagePath):
		"""Carga una cara individual del cubemap"""
		surface = pygame.image.load(imagePath)
		textureData = pygame.image.tostring(surface, "RGB", False)
		
		glTexImage2D(
			target, 0, GL_RGB,
			surface.get_width(), surface.get_height(),
			0, GL_RGB, GL_UNSIGNED_BYTE, textureData
		)
	
	
	def _configureCubemapParameters(self):
		"""Configura los parámetros de filtrado y wrapping del cubemap"""
		params = {
			GL_TEXTURE_MAG_FILTER: GL_LINEAR,
			GL_TEXTURE_MIN_FILTER: GL_LINEAR,
			GL_TEXTURE_WRAP_S: GL_CLAMP_TO_EDGE,
			GL_TEXTURE_WRAP_T: GL_CLAMP_TO_EDGE,
			GL_TEXTURE_WRAP_R: GL_CLAMP_TO_EDGE
		}
		
		for param, value in params.items():
			glTexParameteri(GL_TEXTURE_CUBE_MAP, param, value)
		

	def Render(self):
		if not self._isRenderReady():
			return
		
		self._activateShaderProgram()
		self._updateCameraUniforms()
		self._renderSkyboxGeometry()
	
	
	def _isRenderReady(self):
		"""Verifica si el skybox está listo para renderizar"""
		return self.shaders is not None
	
	
	def _activateShaderProgram(self):
		"""Activa el programa de shaders del skybox"""
		glUseProgram(self.shaders)
	
	
	def _updateCameraUniforms(self):
		"""Actualiza las matrices de la cámara en los shaders"""
		if self.cameraRef is None:
			return
		
		viewLocation = glGetUniformLocation(self.shaders, "viewMatrix")
		projectionLocation = glGetUniformLocation(self.shaders, "projectionMatrix")
		
		glUniformMatrix4fv(viewLocation, 1, GL_FALSE, 
						   glm.value_ptr(self.cameraRef.viewMatrix))
		glUniformMatrix4fv(projectionLocation, 1, GL_FALSE, 
						   glm.value_ptr(self.cameraRef.projectionMatrix))
	
	
	def _renderSkyboxGeometry(self):
		"""Renderiza la geometría del skybox"""
		self._disableDepthWriting()
		self._bindTextures()
		self._setupVertexAttributes()
		self._drawCube()
		self._cleanupVertexAttributes()
		self._enableDepthWriting()
	
	
	def _disableDepthWriting(self):
		"""Desactiva la escritura en el depth buffer"""
		glDepthMask(GL_FALSE)
	
	
	def _enableDepthWriting(self):
		"""Reactiva la escritura en el depth buffer"""
		glDepthMask(GL_TRUE)
	
	
	def _bindTextures(self):
		"""Vincula la textura del cubemap"""
		glBindTexture(GL_TEXTURE_CUBE_MAP, self.texture)
	
	
	def _setupVertexAttributes(self):
		"""Configura los atributos de vértice y buffers"""
		glBindBuffer(GL_ARRAY_BUFFER, self.VBO)
		glBufferData(GL_ARRAY_BUFFER, self.vertexBuffer.nbytes, 
					 self.vertexBuffer, GL_STATIC_DRAW)
		
		glEnableVertexAttribArray(0)
		glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 12, ctypes.c_void_p(0))
	
	
	def _drawCube(self):
		"""Dibuja el cubo del skybox"""
		glDrawArrays(GL_TRIANGLES, 0, self._vertexCount)
	
	
	def _cleanupVertexAttributes(self):
		"""Limpia los atributos de vértice después del renderizado"""
		glDisableVertexAttribArray(0)
		
