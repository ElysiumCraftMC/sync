#version 120

uniform sampler2D DiffuseSampler;
uniform sampler2D FadeSampler;

uniform float Time;
uniform vec2 OutSize;

varying vec2 texCoord;

void main()
{
    float fade = texture2D(FadeSampler, texCoord).r;

    float intensity = 1.0 - fade;
    float shakeMag = intensity * 0.02;

    float sx = sin(Time * 40.0) + sin(Time * 17.0) * 0.6 + sin(Time * 53.0) * 0.3;
    float sy = cos(Time * 31.0) + cos(Time * 63.0) * 0.5 + cos(Time * 22.0) * 0.4;
    vec2 shake = vec2(sx, sy) * shakeMag;

    vec2 shakenUV = texCoord + shake;
    vec4 color = texture2D(DiffuseSampler, shakenUV);

    // --- Lens Flare ---
    vec2 aspect = vec2(OutSize.x / OutSize.y, 1.0);
    vec2 uv = texCoord * aspect;
    vec2 lightPos = vec2(0.5, 0.5) * aspect;
    vec2 toLight = lightPos - uv;
    float dist = length(toLight);
    vec2 dir = normalize(toLight + 1e-6);

    float core = exp(-dist * 5.0) * 0.35;
    float rayLen = 1.0 - smoothstep(0.0, intensity * 1.2 + 0.01, dist);
    float streak = exp(-abs(toLight.x * fade + toLight.y * 0.5) * 30.0) * exp(-dist * 2.0) * 2.0 * rayLen;
    float ring = smoothstep(0.3, 0.28, dist) * smoothstep(0.26, 0.28, dist) * 0.12;


    vec3 flareColor = vec3(1.0, 0.85, 0.5) * (core + streak + ring);
    flareColor *= (sin(Time * 1.5) * 0.1 + 0.9);

    color.rgb += flareColor * intensity;
    // --- End Lens Flare ---

    gl_FragColor = mix(color, vec4(1.0, 1.0, 1.0, 1.0), fade);
}
