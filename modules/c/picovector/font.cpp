#include <algorithm>

#include "font.hpp"
#include "image.hpp"
#include "picovector.hpp"
#include "brush.hpp"
#include "mat3.hpp"

using std::sort;

namespace picovector {

  vec2_t glyph_path_point_t::transform(mat3_t *transform) {
    return vec2_t(
      transform->v00 * float(x) + transform->v01 * float(y) + transform->v02,
      transform->v10 * float(x) + transform->v11 * float(y) + transform->v12
    );
  }

  rect_t glyph_t::bounds(mat3_t *transform) {
    vec2_t p1(x, -y);
    vec2_t p2(x + w, -y);
    vec2_t p3(x + w, -y - h);
    vec2_t p4(x, -y);

    p1 = p1.transform(transform);
    p2 = p2.transform(transform);
    p3 = p3.transform(transform);
    p4 = p4.transform(transform);

    float minx = min(p1.x, min(p2.x, min(p3.x, p4.x)));
    float miny = min(p1.y, min(p2.y, min(p3.y, p4.y)));
    float maxx = max(p1.x, max(p2.x, max(p3.x, p4.x)));
    float maxy = max(p1.y, max(p2.y, max(p3.y, p4.y)));

    return rect_t(minx, miny, ceil(maxx) - minx, ceil(maxy) - miny);
  }

  rect_t font_t::measure(image_t *target, const char *text, float size) {
    rect_t r =  {0, 0, 0, 0};

    mat3_t transform;
    transform = transform.scale(size / 128.0f, size / 128.0f);

    for(size_t i = 0; i < strlen(text); i++) {
      char c = text[i];
      // find the glyph
      for(int j = 0; j < this->glyph_count; j++) {
        if(this->glyphs[j].codepoint == uint16_t(c)) {
          r.w += float(this->glyphs[j].advance) * (size / 128.0f);
          r.h = size;
        }
      }
    }

    return r;
  }

  static uint16_t get_utf8_char(const char *text, const char *end) {
    uint16_t codepoint;
    if((*text & 0x80) == 0x00) {
      codepoint = *text; // ASCII, codepoints U+0000...U007F
    }
    else if( ((*text & 0xE0) == 0xC0) && (text+1 <= end) && ((*(text+1) & 0xC0) == 0x80) ) {
      codepoint = ((uint16_t)(*text & 0x1F) << 6) + (*(text+1) & 0x3F); //codepoints U+0080...U+07FF
    }
    else if( ((*text & 0xF0) == 0xE0) && (text+2 <= end) && ((*(text+1) & 0xC0) == 0x80) && ((*(text+2) & 0xC0) == 0x80) ) {
      codepoint = ((uint16_t)(*text & 0x0F) << 12) + ((uint16_t)(*(text+1) & 0x3F) << 6) + (*(text+2) & 0x3F); // codepoints U+0800...U+FFFF
    }
    else {
      codepoint = 0xFFFF; // malformed UTF-8 sequences or unsupported codepoints starting at U+10000
    }
    return codepoint;
  }

  static inline uint8_t utf8_seq_len(uint8_t b0) {
    if ((b0 & 0x80) == 0x00) return 1;
    if ((b0 & 0xE0) == 0xC0) return 2;
    if ((b0 & 0xF0) == 0xE0) return 3;
    if ((b0 & 0xF8) == 0xF0) return 4;
    return 0; // invalid
  }

  void font_t::draw(image_t *target, const char *text, float x, float y, float size) {
    vec2_t caret(x, y);

    mat3_t transform;
    transform = transform.translate(x, y);
    transform = transform.translate(0, size);
    transform = transform.scale(size / 128.0f, size / 128.0f);

    const char *end = text + strlen(text);

    while(text != end) {
      // find the uft8 codepoint
      uint16_t codepoint = get_utf8_char(text, end);

      // find the glyph
      for(int j = 0; j < this->glyph_count; j++) {
        if(this->glyphs[j].codepoint == codepoint) {
          render_glyph(&this->glyphs[j], target, &transform, target->brush());
          float a = this->glyphs[j].advance;
          transform = transform.translate(a, 0);
          break;
        }
      }

      text += utf8_seq_len(*text);
    }
  }

}
