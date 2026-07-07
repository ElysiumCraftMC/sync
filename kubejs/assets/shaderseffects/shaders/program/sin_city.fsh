#version 120

uniform sampler2D DiffuseSampler;

varying vec2 texCoord;

void main()
{
    vec4 color = texture2D(DiffuseSampler, texCoord);

    float gray = dot(color.rgb, vec3(0.299, 0.587, 0.114));

    float isRed = step(0.2, color.r) * step(color.g, 0.2) * step(color.b, 0.2);

    gl_FragColor = vec4(mix(vec3(gray), color.rgb, isRed), color.a);
}
