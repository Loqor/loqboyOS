#version 430

out vec4 fragColor;

uniform vec2 resolution;
uniform vec2 mouse;
uniform float time;

float sdSphere(vec3 p, float s) {
    return length(p) - s;
}

float sdBox(vec3 p, vec3 b) {
    vec3 q = abs(p) - b;
    return length(max(q, 0.0)) + min(max(q.x, max(q.y, q.z)), 0.0);
}

float smin(float a, float b, float k) {
    float h = max(k - abs(a - b), 0.0) / k;
    return min(a, b) - h * h * h * k * (1.0 / 6.0);
}
float map (vec3 p) {
    vec3 spherePos = vec3(sin(time) * 3.0, 0, 0);
    float sphere = sdSphere((p - spherePos) * 4.0, 1.0) / 4.0;

    float box = sdBox(p * 4.0, vec3(0.75)) / 4.0;

    float ground = p.y + 0.75;

    return smin(ground, smin(sphere, box, 2.0), 1.0);
}

void main() {
    vec2 uv = (gl_FragCoord.xy * 2.0 - resolution.xy) / resolution.y;
    vec2 m = (mouse.xy * 2.0 - resolution.xy) / resolution.y;

    vec3 ro = vec3(0, 0, -3);
    vec3 rd = normalize(vec3(uv, 1));
    vec3 col = vec3(0.0);

    float t = 0.0;

    for(int i = 0; i < 80; i ++) {
        vec3 p = ro + rd * t;

        float d = map(p);

        t += d;

        if(d < 0.001 || t > 100.) break;
    }

    col = vec3(t * 0.2);

    fragColor = vec4(col, 1);
}