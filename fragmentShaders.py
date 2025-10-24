# GLSL

fragment_shader = '''
#version 330 core

in vec2 outTexCoords;

out vec4 fragColor;

uniform sampler2D tex0;

void main()
{
    fragColor = texture(tex0, outTexCoords);
}

'''