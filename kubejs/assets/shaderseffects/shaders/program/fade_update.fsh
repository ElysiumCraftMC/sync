#version 120

uniform sampler2D DiffuseSampler;

varying vec2 texCoord;

void main()
{
    float current = texture2D(DiffuseSampler, texCoord).r;
    float step = 0.003;
    float next = min(1.0, current + step);

    gl_FragColor = vec4(next, next, next, 1.0);
}
