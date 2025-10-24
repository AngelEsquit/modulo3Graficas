import glm # pip install PyGLM
from OpenGL.GL import *
from numpy import array, float32


class Buffer(object):
	def __init__(self, data):
		self.data = data

		# Vertex Buffer 
		self.vertexBuffer = array(self.data, dtype = float32)

		# Vertex Buffer Object
		self.VBO = glGenBuffers(1)


	def Use(self, attribNumber, size):

		glBindBuffer(GL_ARRAY_BUFFER, self.VBO)

		# Mandar la informacion de vertices
		glBufferData(GL_ARRAY_BUFFER,               # Buffer ID
					 self.vertexBuffer.nbytes,      # Buffer size in bytes
					 self.vertexBuffer,             # Buffer data
					 GL_STATIC_DRAW)                # Usage

		# Atributo
		glVertexAttribPointer(attribNumber,			# Attribute Number
							  size,					# Size
							  GL_FLOAT,				# Type
							  GL_FALSE,				# Is it normalized?
							  0,					# Stride
							  ctypes.c_void_p(0))	# Offset

		glEnableVertexAttribArray(attribNumber)
		