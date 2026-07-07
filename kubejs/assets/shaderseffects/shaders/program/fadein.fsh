#version 120

uniform sampler2D DiffuseSampler;
uniform sampler2D FadeSampler;

varying vec2 texCoord;

void main()
{
    vec4 color = texture2D(DiffuseSampler, texCoord);
    float fade = texture2D(FadeSampler, texCoord).r;
    float alpha = fade;
    gl_FragColor = mix(color, vec4(1.0, 1.0, 1.0, 1.0), alpha);
}
