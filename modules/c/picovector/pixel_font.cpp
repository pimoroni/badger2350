#include <algorithm>

#include "pixel_font.hpp"
#include "image.hpp"
#include "picovector.hpp"
#include "brush.hpp"
#include "mat3.hpp"

using std::min;
using std::max;

namespace picovector {

  int pixel_font_t::glyph_index(int codepoint) {

    uint32_t low = 0;
    uint32_t high = this->glyph_count;

    while(low < high) {
      uint32_t mid = low + (high - low) / 2;
      uint32_t compare = this->glyphs[mid].codepoint;
      if (compare == (uint32_t)codepoint) {
        return mid;
      }

      if(compare < (uint32_t)codepoint) {
        low = mid + 1;
      } else {
        high = mid;
      }
    }

    return -1;  // not found
  }

  rect_t pixel_font_t::measure(image_t *target, const char *text) {
    rect_t tb = target->clip();
    rect_t b(tb.x + tb.w, tb.y + tb.h, 0, this->height);

    vec2_t caret(0, 0);
    while(*text != '\0') {
      // special case for "space"
      if(*text == 32) {
        caret.x += this->width / 3;
        text++;
        continue;
      }

      int glyph_index = this->glyph_index(*text);
      if(glyph_index != -1) {
        pixel_font_glyph_t *glyph = &this->glyphs[glyph_index];
        caret.x += glyph->width + 1;

        b.x = min(caret.x, b.x);
        b.w = max(caret.x, b.w);
      }
      text++;
    }
    return b;
  }

  void pixel_font_t::draw_glyph(image_t *target, const pixel_font_glyph_t *glyph, uint8_t *data, brush_t *brush, const rect_t &bounds, int x, int y) {
    // calculate the number of bytes per glyph pixel data row
    uint32_t bytes_per_row = (this->width + 7) >> 3;

    // clip the x and y ranges to within bounds
    int yoff = 0;//max(0, int(bounds.y - y));
    if(y < bounds.y) {
      yoff = bounds.y - y;
    }
    int yf = y + yoff;
    int yc = this->height - yoff;
    yc = min(yc, int(bounds.y + bounds.h - yf));

    int xoff = max(0, int(bounds.x - x));
    int xf = x + xoff;
    int xc = glyph->width - xoff;
    xc = min(xc, int(bounds.x + bounds.w - xf));

    //uint32_t *dst = (uint32_t *)target->ptr(0, yf);
    uint32_t row_stride = target->row_stride() / 4;

    span_func_t fn = target->_span_func;

    data += yoff * bytes_per_row;
    for(int yo = yf; yo < yf + yc; yo++) {
      for(int xo = xf; xo < xf + xc; xo++) {
        int bit = xo - x;
        uint8_t b = data[bit >> 3];
        if(b & (0b1 << (7 - (bit & 0b111)))) {
          //brush->pixel(&dst[xo]);
          //brush->render_span(target, xo, yo, 1);
          fn(target, brush, xo, yo, 1);
        }
      }

      //dst += row_stride;
      data += bytes_per_row;
    }
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

  void pixel_font_t::draw(image_t *target, const char *text, int x, int y) {
    // check if text is within clipping area
    rect_t text_bounds = this->measure(target, text);
    text_bounds.x = x;
    text_bounds.y = y;

    // text isn't within the target bounds at all, escape early
    if(!text_bounds.intersects(target->clip())) {
      return;
    }

    rect_t bounds = target->clip();

    brush_t *brush = target->brush();

    const char *end = text + strlen(text);

    while(*text != '\0') {
      // special case for "space"
      if(*text == 32) {
        x += this->width / 3;
        text++;
        continue;
      }

      int codepoint = get_utf8_char(text, end);
      int glyph_index = this->glyph_index(codepoint);
      if(glyph_index != -1) {
        pixel_font_glyph_t *glyph = &this->glyphs[glyph_index];
        uint8_t *data = &this->glyph_data[this->glyph_data_size * glyph_index];

        draw_glyph(target, glyph, data, brush, bounds, x, y);

        x += glyph->width + 1;
      }

      text += utf8_seq_len(*text);
    }

  }

}