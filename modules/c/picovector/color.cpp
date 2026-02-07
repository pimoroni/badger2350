#include "color.hpp"

namespace picovector {

  void color_t::premul(uint8_t r, uint8_t g, uint8_t b, uint8_t a) {
    uint8_t rp = (r * a) / 255;
    uint8_t gp = (g * a) / 255;
    uint8_t bp = (b * a) / 255;
    _p = __builtin_bswap32((rp << 24) | (gp << 16) | (bp << 8) | a);

    uint8_t* pp = (uint8_t*)&_p;
    // printf("bytes as uint8 %d, %d, %d, %d\n", pp[0], pp[1], pp[2], pp[3]);
    // printf("bytes as uint32 %d, %d, %d, %d\n", ((_p >> 24) & 0xff), ((_p >> 16) & 0xff), ((_p >> 8) & 0xff), ((_p >> 0) & 0xff));
  }

  rgb_color_t::rgb_color_t(uint8_t r, uint8_t g, uint8_t b, uint8_t a) : _r(r), _g(g), _b(b), _a(a) {
    premul(r, g, b, a);
  }

  hsv_color_t::hsv_color_t(uint8_t h, uint8_t s, uint8_t v, uint8_t a) : _h(h), _s(s), _v(v), _a(a) {
    int hs = (h * 360) / 255;
    int region = hs / 60;
    int remainder = (hs - (region * 60)) * 255 / 60;

    int p = (v * (255 - s)) / 255;
    int q = (v * (255 - (s * remainder) / 255)) / 255;
    int t = (v * (255 - (s * (255 - remainder)) / 255)) / 255;

    uint8_t r, g, b;
    switch (region) {
      case 0:  r = v; g = t; b = p; break;
      case 1:  r = q; g = v; b = p; break;
      case 2:  r = p; g = v; b = t; break;
      case 3:  r = p; g = q; b = v; break;
      case 4:  r = t; g = p; b = v; break;
      default: r = v; g = p; b = q; break;
    }

    premul(r, g, b, a);
  }


  static inline float clamp01(float x) {
      if (x < 0.0f) return 0.0f;
      if (x > 1.0f) return 1.0f;
      return x;
  }


  static inline float srgb_encode(float x) {
      x = clamp01(x);
      if (x <= 0.0031308f) {
          return 12.92f * x;
      } else {
          return 1.055f * powf(x, 1.0f / 2.4f) - 0.055f;
      }
  }

  oklch_color_t::oklch_color_t(uint8_t l, uint8_t c, uint8_t h, uint8_t a) : _l(l), _c(c), _h(h), _a(a) {
    // Normalise to OKLCH ranges
    float L = (float)l / 255.0f;   // 0–1

    float t = (float)c / 255.0f;      // 0–1
    // Slightly compress the top end: more resolution at low/mid chroma
    t = 1.0f - (1.0f - t) * (1.0f - t);  // simple quadratic ease-out
    const float OKLCH_MAX_CHROMA = 0.35f;
    float C = t * OKLCH_MAX_CHROMA;

    // Wrap hue and convert to radians
    float hs = (float)((h * 360) / 255) * (float)M_PI / 180.0f;

    // OKLCH → OKLab
    float a_ = C * cosf(hs);
    float b_ = C * sinf(hs);

    // OKLab → LMS (non-linear)
    float l_ = L + 0.3963377774f * a_ + 0.2158037573f * b_;
    float m_ = L - 0.1055613458f * a_ - 0.0638541728f * b_;
    float s_ = L - 0.0894841775f * a_ - 1.2914855480f * b_;

    // Cube to get linear LMS
    l_ = l_ * l_ * l_;
    m_ = m_ * m_ * m_;
    s_ = s_ * s_ * s_;

    // LMS → linear sRGB
    float r_lin =  4.0767416621f * l_ - 3.3077115913f * m_ + 0.2309699292f * s_;
    float g_lin = -1.2684380046f * l_ + 2.6097574011f * m_ - 0.3413193965f * s_;
    float b_lin = -0.0041960863f * l_ - 0.7034186147f * m_ + 1.7076147010f * s_;

    // Linear → sRGB
    float r_srgb = srgb_encode(r_lin);
    float g_srgb = srgb_encode(g_lin);
    float b_srgb = srgb_encode(b_lin);

    // Convert to 0–255
    int ri = (int)(r_srgb * 255.0f + 0.5f);
    int gi = (int)(g_srgb * 255.0f + 0.5f);
    int bi = (int)(b_srgb * 255.0f + 0.5f);

    // Clamp to valid byte range
    if (ri < 0) ri = 0; else if (ri > 255) ri = 255;
    if (gi < 0) gi = 0; else if (gi > 255) gi = 255;
    if (bi < 0) bi = 0; else if (bi > 255) bi = 255;

    premul(ri, gi, bi, a);
  }
}

/*



inline uint32_t oklch(int l_in, int c_in, int h_in, uint8_t a_in = 255) {
  // Normalise to OKLCH ranges
  float L = (float)l_in / 255.0f;   // 0–1

  float t = (float)c_in / 255.0f;      // 0–1
  // Slightly compress the top end: more resolution at low/mid chroma
  t = 1.0f - (1.0f - t) * (1.0f - t);  // simple quadratic ease-out
  const float OKLCH_MAX_CHROMA = 0.35f;
  float C = t * OKLCH_MAX_CHROMA;

  // Wrap hue and convert to radians
  if (h_in < 0) {
    h_in %= 360;
    if (h_in < 0) h_in += 360;
  }
  h_in %= 360;
  float h = (float)h_in * (float)M_PI / 180.0f;

  // OKLCH → OKLab
  float a = C * cosf(h);
  float b = C * sinf(h);

  // OKLab → LMS (non-linear)
  float l_ = L + 0.3963377774f * a + 0.2158037573f * b;
  float m_ = L - 0.1055613458f * a - 0.0638541728f * b;
  float s_ = L - 0.0894841775f * a - 1.2914855480f * b;

  // Cube to get linear LMS
  l_ = l_ * l_ * l_;
  m_ = m_ * m_ * m_;
  s_ = s_ * s_ * s_;

  // LMS → linear sRGB
  float r_lin =  4.0767416621f * l_ - 3.3077115913f * m_ + 0.2309699292f * s_;
  float g_lin = -1.2684380046f * l_ + 2.6097574011f * m_ - 0.3413193965f * s_;
  float b_lin = -0.0041960863f * l_ - 0.7034186147f * m_ + 1.7076147010f * s_;

  // Linear → sRGB
  float r_srgb = srgb_encode(r_lin);
  float g_srgb = srgb_encode(g_lin);
  float b_srgb = srgb_encode(b_lin);

  // Convert to 0–255
  int ri = (int)(r_srgb * 255.0f + 0.5f);
  int gi = (int)(g_srgb * 255.0f + 0.5f);
  int bi = (int)(b_srgb * 255.0f + 0.5f);

  // Clamp to valid byte range
  if (ri < 0) ri = 0; else if (ri > 255) ri = 255;
  if (gi < 0) gi = 0; else if (gi > 255) gi = 255;
  if (bi < 0) bi = 0; else if (bi > 255) bi = 255;

  return rgba(ri, gi, bi, a_in);
}*/