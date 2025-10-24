# GLSL

fragment_shader = '''
#version 330 core

in vec2 fragTexCoords;
in vec3 fragNormal;
in vec4 fragPosition;

out vec4 fragColor;

uniform sampler2D tex0;
uniform vec3 pointLight;
uniform float ambientLight;

void main()
{
    vec3 lightDir = normalize(pointLight - fragPosition.xyz);
    float intensity = max( 0 , dot(fragNormal, lightDir)) + ambientLight;

    fragColor = texture(tex0, fragTexCoords) * intensity;
}

'''


toon_shader = '''
#version 330 core

in vec2 fragTexCoords;
in vec3 fragNormal;
in vec4 fragPosition;

out vec4 fragColor;

uniform sampler2D tex0;
uniform vec3 pointLight;
uniform float ambientLight;

void main()
{
    vec3 lightDir = normalize(pointLight - fragPosition.xyz);
    float intensity = max( 0 , dot(fragNormal, lightDir)) + ambientLight;

    if (intensity < 0.33)
        intensity = 0.2;
    else if (intensity < 0.66)
        intensity = 0.6;
    else
        intensity = 1.0;

    fragColor = texture(tex0, fragTexCoords) * intensity;
}

'''


negative_shader = '''
#version 330 core

in vec2 fragTexCoords;
in vec3 fragNormal;
in vec4 fragPosition;

out vec4 fragColor;

uniform sampler2D tex0;

void main()
{
    fragColor = 1 - texture(tex0, fragTexCoords);
}

'''


magma_shader = '''
#version 330 core

in vec2 fragTexCoords;
in vec3 fragNormal;
in vec4 fragPosition;

out vec4 fragColor;

uniform sampler2D tex0;
uniform sampler2D tex1;

uniform vec3 pointLight;
uniform float ambientLight;

uniform float time;

void main()
{
    vec3 lightDir = normalize(pointLight - fragPosition.xyz);
    float intensity = max( 0 , dot(fragNormal, lightDir)) + ambientLight;

    fragColor = texture(tex0, fragTexCoords) * intensity;
    fragColor += texture(tex1, fragTexCoords) * ((sin(time) + 1) / 2);
}

'''





# NEW fragment shaders (custom, independent of class examples)

fresnel_fragment_shader = '''
#version 330 core

in vec2 fragTexCoords;
in vec3 fragNormal;
in vec4 fragPosition;

out vec4 fragColor;

uniform sampler2D tex0;
uniform vec3 pointLight;
uniform float ambientLight;
uniform vec3 cameraPos; // world-space camera position

void main()
{
    // Basic lambert lighting
    vec3 N = normalize(fragNormal);
    vec3 L = normalize(pointLight - fragPosition.xyz);
    float lambert = max(0.0, dot(N, L));
    float intensity = lambert + ambientLight;

    // Fresnel rim: view-dependent edge highlight
    vec3 V = normalize(cameraPos - fragPosition.xyz);
    float fresnel = pow(1.0 - max(dot(N, V), 0.0), 3.0);
    vec3 rimColor = mix(vec3(0.1, 0.6, 1.0), vec3(1.0), 0.2) * fresnel * 1.5;

    vec3 base = texture(tex0, fragTexCoords).rgb * intensity;
    fragColor = vec4(base + rimColor, 1.0);
}

'''


checker_fragment_shader = '''
#version 330 core

in vec2 fragTexCoords;
in vec3 fragNormal;
in vec4 fragPosition;

out vec4 fragColor;

uniform sampler2D tex0;
uniform float time;
uniform float ambientLight;
uniform vec3 pointLight;

// Animated UV checker overlay mixed with base texture
void main()
{
    vec3 N = normalize(fragNormal);
    vec3 L = normalize(pointLight - fragPosition.xyz);
    float intensity = max(0.0, dot(N, L)) + ambientLight;

    // UV-based checker, animated scale
    float scale = 10.0 + 2.0 * sin(time * 0.8);
    vec2 uv = fragTexCoords * scale;
    float checker = step(0.5, fract(uv.x)) + step(0.5, fract(uv.y));
    checker = mod(checker, 2.0); // 0 or 1
    vec3 checkerColor = mix(vec3(0.1, 0.1, 0.1), vec3(1.0, 0.9, 0.6), checker);

    vec3 base = texture(tex0, fragTexCoords).rgb * intensity;
    // Blend overlay subtly
    vec3 color = mix(base, base * checkerColor, 0.35);
    fragColor = vec4(color, 1.0);
}

'''


scanlines_fragment_shader = '''
#version 330 core

in vec2 fragTexCoords;
in vec3 fragNormal;
in vec4 fragPosition;

out vec4 fragColor;

uniform sampler2D tex0;
uniform float time;
uniform float ambientLight;
uniform vec3 pointLight;

void main()
{
    vec3 N = normalize(fragNormal);
    vec3 L = normalize(pointLight - fragPosition.xyz);
    float intensity = max(0.0, dot(N, L)) + ambientLight;

    // Horizontal scanlines that drift over time in screenspace-ish using clip-space y
    float lines = sin(fragPosition.y * 40.0 + time * 6.0);
    float mask = smoothstep(0.0, 0.2, lines);
    vec3 tint = mix(vec3(0.2, 0.9, 0.8), vec3(0.1, 0.1, 0.3), mask);

    vec3 base = texture(tex0, fragTexCoords).rgb * intensity;
    fragColor = vec4(base * tint, 1.0);
}

'''


unlit_fragment_shader = '''
#version 330 core

in vec2 fragTexCoords;
in vec3 fragNormal;
in vec4 fragPosition;

out vec4 fragColor;

uniform sampler2D tex0;

void main()
{
    fragColor = texture(tex0, fragTexCoords);
}

'''




