#version 430

out vec4 fragColor;

uniform vec2 resolution;
uniform vec2 mouse;
uniform float time;

vec2 rotate2D(vec2 uv, float a) {
    float s = sin(a);
    float c = cos(a);
    return mat2(c, -s, s, c) * uv;
}

void main() {
    vec2 uv = (gl_FragCoord.xy - 0.5 * resolution.xy) / resolution.y;
    vec3 col = vec3(0.0);

    uv = rotate2D(uv, 3.14 / 2.0 + time);

    float r = 0.17;
    for (float i=0.0; i< 60.0; i++) {
        float a = i / 3;
        float dx = 2 * r * cos(a) - r * cos(2 * a);
        float dy = 2 * r * sin(a) - r * sin(2 * a);

        float b = 0.001 / length(uv - vec2(dx + 0.1, dy));

        col += b;
    }

    col *= vec3(0.0, 0.93333, 0.0);

    fragColor = vec4(col, 1.0);
}