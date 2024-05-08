#version 430

uniform sampler2D DiffuseSampler;
uniform vec2 InSize;
uniform float time;
uniform vec3 colorization;
uniform float brightness;
uniform bool shuckScreen;
uniform float timeRunning;

in vec2 texCoord;
out vec4 fragColor;

const vec4 Zero = vec4(0.0);
const vec4 Half = vec4(0.5);
const vec4 One = vec4(1.0);
const vec4 Two = vec4(2.0);

const float Pi = 3.1415926535;
const float PincushionAmount = 0.02;
const float CurvatureAmount = 0.02;
const float ScanlineAmount = 0.8;
const float ScanlineScale = 480;
const float ScanlineHeight = 1.0;
const float ScanlineBrightScale = 1.0;
const float ScanlineBrightOffset = 0.0;
const float ScanlineOffset = 0.0;
const vec3 Floor = vec3(0.05, 0.05, 0.05);
const vec3 Power = vec3(0.8, 0.8, 0.8);

const float bloomThreshold = 0.1; // Brightness threshold for bloom
const float bloomIntensity = 0.075; // Intensity of bloom effect
const int bloomBlurSize = 1; // Number of samples for bloom blur

vec4 applyBloom(vec2 coord, vec4 baseColor, vec3 colorization) {
    vec4 bloomColor = Zero;
    for (int x = -bloomBlurSize; x <= bloomBlurSize; x++) {
        for (int y = -bloomBlurSize; y <= bloomBlurSize; y++) {
            vec2 sampleCoord = coord + vec2(x, y) * 0.0075; // Adjust this value to control the spread of the bloom
            vec4 sampleOf = texture(DiffuseSampler, sampleCoord);
            if (sampleOf.r > bloomThreshold || sampleOf.g > bloomThreshold || sampleOf.b > bloomThreshold) {
                bloomColor += sampleOf * bloomIntensity;
            }
        }
    }
    // Multiply the bloom color by the colorization vector to tint the bloom effect
    bloomColor.rgb *= colorization;
    return baseColor + bloomColor;
}

void main() {
    vec2 modifiedTexCoord = texCoord;
    float scanlineScaleFactor = 0.0;

    // Check if shuckScreen is greater than 0 and scroll the screen
    if (shuckScreen) {
        float baseSpeed = timeRunning; // Initial speed of the scrolling
        float scrollSpeed = 0;

        scrollSpeed = min(baseSpeed, 1.0);

        modifiedTexCoord.y += time * scrollSpeed;

        // Optional: Wrap around the texture coordinate to create a continuous scroll
        modifiedTexCoord.y = fract(modifiedTexCoord.y);

        // Setting ScanlineScale to -1 when shuckScreen is greater than 0
        scanlineScaleFactor = -1;

        if(baseSpeed >= 0.28) {
            modifiedTexCoord = texCoord;
        }
    }

    vec2 PinUnitCoord = modifiedTexCoord * Two.xy - One.xy;
    float PincushionR2 = pow(length(PinUnitCoord), 2.0);
    vec2 CurvatureClipCurve = PinUnitCoord * CurvatureAmount * PincushionR2;
    vec2 ScreenClipCoord = modifiedTexCoord;
    ScreenClipCoord -= Half.xy;
    ScreenClipCoord *= One.xy - CurvatureAmount * 0.2;
    ScreenClipCoord += Half.xy;
    ScreenClipCoord += CurvatureClipCurve;

    if (ScreenClipCoord.x < 0.0 ||
    ScreenClipCoord.y < 0.0 ||
    ScreenClipCoord.x > 1.0 ||
    ScreenClipCoord.y > 1.0) discard;

    vec4 InTexel = texture(DiffuseSampler, ScreenClipCoord);

    float InnerSine = modifiedTexCoord.y * InSize.y * (ScanlineScale - scanlineScaleFactor) * 0.25;
    float ScanBrightMod = sin(InnerSine * Pi + (time * 0.12) * InSize.y * 0.25);
    float ScanBrightness = brightness * mix(1.0, (pow(ScanBrightMod * ScanBrightMod, ScanlineHeight)
    * (ScanlineBrightScale + (scanlineScaleFactor / 1000) + 1.0)) * 0.5, ScanlineAmount);
    vec3 ScanlineTexel = InTexel.rgb * ScanBrightness;

    vec3 grayscale = vec3(dot(ScanlineTexel, vec3(0.8, 0.8, 0.8)));  // Adjusted grayscale conversion
    grayscale = pow(grayscale, Power);  // Gamma correction

    vec4 colorOutput = vec4(colorization * grayscale, 1.0);
    fragColor = applyBloom(ScreenClipCoord, colorOutput, colorization);
}