#include <string.h>
#include <math.h>
#include <algorithm>
#include <vector>

#include "rasteriser.hpp"
#include "algorithms/algorithms.hpp"
#include "image.hpp"
#include "blend.hpp"
#include "blit.hpp"
#include "brush.hpp"
#include "shape.hpp"

using std::vector;

namespace picovector {

  image_t::image_t() {
  }

  image_t::image_t(image_t *source, rect_t r) {
    rect_t i = source->_bounds.intersection(r);
    *this = *source;
    _bounds = rect_t(0, 0, i.w, i.h);
    _clip = rect_t(0, 0, i.w, i.h);
    _buffer = source->ptr(i.x, i.y);
    _managed_buffer = false;
  }

  image_t::image_t(int w, int h, pixel_format_t pixel_format, bool has_palette) {
    _bounds = rect_t(0, 0, w, h);
    _clip = rect_t(0, 0, w, h);
    _brush = nullptr;
    _pixel_format = pixel_format;
    _has_palette = has_palette;
    _managed_buffer = true;
    _bytes_per_pixel = this->_has_palette ? sizeof(uint8_t) : sizeof(uint32_t);
    _row_stride = w * _bytes_per_pixel;
    _buffer = PV_MALLOC(this->buffer_size());
    if(_has_palette) {
      _palette.resize(256);
    }
  }

  image_t::image_t(void *buffer, int w, int h, pixel_format_t pixel_format, bool has_palette) {
    _bounds = rect_t(0, 0, w, h);
    _clip = rect_t(0, 0, w, h);
    _brush = nullptr;
    _pixel_format = pixel_format;
    _has_palette = has_palette;
    _buffer = buffer;
    _managed_buffer = false;
    _bytes_per_pixel = this->_has_palette ? sizeof(uint8_t) : sizeof(uint32_t);
    _row_stride = w * _bytes_per_pixel;
    if(_has_palette) {
      _palette.resize(256);
    }
  }

  image_t::~image_t() {
    if(this->_managed_buffer) {
#ifdef PICO
      PV_FREE(this->_buffer);
#else
      PV_FREE(this->_buffer, this->buffer_size());
#endif
    }
  }

  size_t image_t::buffer_size() {
    return this->_bytes_per_pixel * this->_bounds.w * this->_bounds.h;
  }

  size_t image_t::bytes_per_pixel() {
    return this->_bytes_per_pixel;
  }

  bool image_t::is_compatible(image_t *other) {
    return this->_palette == other->_palette && this->_pixel_format == other->_pixel_format;
  }

  uint32_t image_t::row_stride() {
    return this->_row_stride;
  }

  rect_t image_t::bounds() {
    return this->_bounds;
  }

  rect_t image_t::clip() {
    return this->_clip;
  }

  void image_t::clip(rect_t r) {
    this->_clip = _bounds.intersection(r);
  }

  bool image_t::has_palette() {
    return this->_has_palette;
  }

  // TODO: why?
  // void image_t::delete_palette() {
  //   if(this->has_palette()) {
  //     this->_palette.clear();
  //   }
  // }

  void image_t::palette(uint8_t i, uint32_t c) {
    this->_palette[i] = c;
  }

  uint32_t image_t::palette(uint8_t i) {
    return this->_palette[i];
  }

  uint8_t image_t::alpha() {
    return this->_alpha;
  }

  void image_t::alpha(uint8_t alpha) {
    // TODO: check if pixel format and palette mode supports alpha
    this->_alpha = alpha;
  }

  antialias_t image_t::antialias() {
    return this->_antialias;
  }

  void image_t::antialias(antialias_t antialias) {
    // TODO: check if pixel format and palette mode supports alpha
    this->_antialias = antialias;
  }

  pixel_format_t image_t::pixel_format() {
    return this->_pixel_format;
  }

  void image_t::pixel_format(pixel_format_t pixel_format) {
    this->_pixel_format = pixel_format;
  }

  brush_t* image_t::brush() {
    return this->_brush;
  }

  void image_t::brush(brush_t *brush) {
    this->_brush = brush;
    this->_span_func = brush->span_func();
    this->_masked_span_func = brush->masked_span_func();
    // this->_span_func = brush->get_span_func(this);
    // this->_mask_span_func = brush->get_mask_span_func(this);
  }

  font_t* image_t::font() {
    return this->_font;
  }

  void image_t::font(font_t *font) {
    this->_font = font;
  }

  pixel_font_t* image_t::pixel_font() {
    return this->_pixel_font;
  }

  void image_t::pixel_font(pixel_font_t *pixel_font) {
    this->_pixel_font = pixel_font;
  }

  image_t image_t::window(rect_t r) {
    rect_t i = _bounds.intersection(r);
    image_t window = image_t(this, rect_t(i.x, i.y, i.w, i.h));
    return window;
  }

  // void image_t::clear(uint32_t c) {
  //   int count = this->_bounds.w * this->_bounds.h;

  //   printf("clear %p (%d)\n", this->_brush, count);
  //   this->_brush->span_func(this->_brush, 0, 0, count);

  //   // if(_has_palette) {
  //   //   memset(_buffer, c, count);
  //   // }else{
  //   //   int dw8 = count >> 3;   // number of blocks of eight pixels
  //   //   int r = count & 0b111;  // remainder
  //   //   uint32_t* p = (uint32_t*)_buffer;
  //   //   while(dw8--) { // unrolled blocks of 8 pixels
  //   //     *p++ = c; *p++ = c; *p++ = c; *p++ = c;
  //   //     *p++ = c; *p++ = c; *p++ = c; *p++ = c;
  //   //   }
  //   //   while(r--) { // fill in remainder
  //   //     *p++ = c;
  //   //   }
  //   // }
  // }

  void image_t::clear() {
    rectangle(_clip);
  }


  void clip_blit_rect(rect_t &r1, rect_t b, rect_t &r2) {
    // perform any source rect clipping that's needed
    float sx = r2.w / r1.w;
    float sy = r2.h / r1.h;

    if(r1.x < b.x) {
      float d = b.x - r1.x;
      r1.x += d;
      r1.w -= d;
      r2.x += (d * sx);
      r2.w -= (d * sx);
    }

    if(r1.y < b.y) {
      float d = b.y - r1.y;
      r1.y += d;
      r1.h -= d;
      r2.y += (d * sy);
      r2.h -= (d * sy);
    }

    if(r1.x + r1.w > b.x + b.w) {
      float d = (r1.x + r1.w) - (b.x + b.w);
      r1.w -= d;
      r2.w -= (d * sx);
    }

    if(r1.y + r1.h > b.y + b.h) {
      float d = (r1.y + r1.h) - (b.y + b.h);
      r1.h -= d;
      r2.h -= (d * sy);
    }
  }

  void image_t::blit(image_t *target, const vec2_t p) {
    rect_t sr = _bounds;
    sr = sr.floor();

    rect_t tr(floorf(p.x), floorf(p.y), sr.w, sr.h); // target rect

    clip_blit_rect(sr, _bounds, tr);
    clip_blit_rect(tr, target->_bounds, sr);
    if(sr.w <= 0 || sr.h <= 0 || tr.w <= 0 || tr.h <= 0) {
      return;
    }

    blend_func_t bf = target->_blend_func;

    for(int y = 0; y < tr.h; y++) {
      if(_has_palette) {
        span_blit(this, target, bf, sr.x, sr.y + y, tr.x, tr.y + y, tr.w, _palette);
      }else{
        span_blit(this, target, bf, sr.x, sr.y + y, tr.x, tr.y + y, tr.w);
      }
    }
  }


  // blit from source rectangle into target rectangle
  void image_t::blit(image_t *target, rect_t sr, rect_t tr) {
    bool flip_h = tr.w < 0;
    bool flip_v = tr.h < 0;

    // clip target rect to target bounds
    // printf("pre clip\n");
    // printf("- sr = %.2f, %.2f (%.2f x %.2f)\n", sr.x, sr.y, sr.w, sr.h);
    // printf("- tr = %.2f, %.2f (%.2f x %.2f)\n", tr.x, tr.y, tr.w, tr.h);
    tr.w = fabs(tr.w);
    tr.h = fabs(tr.h);
    sr = sr.round();
    tr = tr.round();
    clip_blit_rect(sr, _bounds, tr);
    clip_blit_rect(tr, target->_bounds, sr);
    if(sr.w <= 0 || sr.h <= 0 || tr.w <= 0 || tr.h <= 0) {
      return;
    }
    // printf("post clip\n");
    // printf("- sr = %.2f, %.2f (%.2f x %.2f)\n", sr.x, sr.y, sr.w, sr.h);
    // printf("- tr = %.2f, %.2f (%.2f x %.2f)\n", tr.x, tr.y, tr.w, tr.h);

    blend_func_t bf = target->_blend_func;

    // render the scaled spans
    int srcstepx = (sr.w / tr.w) * 65536.0f;
    int srcstepy = (sr.h / tr.h) * 65536.0f;

    int srcx = sr.x * 65536.0f;
    int srcy = sr.y * 65536.0f;

    if(flip_h) {
      srcstepx = -srcstepx;
      srcx = ((_bounds.w - sr.x) * 65536.0f) + srcstepx;
    }

    if(flip_v) {
      srcstepy = -srcstepy;
      srcy = ((_bounds.h - sr.y) * 65536.0f) + srcstepy;
    }

    for(int y = tr.y; y < tr.y + tr.h; y++) {
      if(this->_has_palette) {
        span_blit_scale(this, target, bf, srcx, srcstepx, srcy, tr.x, y, tr.w, _palette);
      }else{
        span_blit_scale(this, target, bf, srcx, srcstepx, srcy, tr.x, y, tr.w);
      }

      srcy += srcstepy;
    }
  }


  void image_t::blit(image_t *target, rect_t tr) {
    blit(target, _bounds, tr);
  }

  /*
    blits a horizontal span of pixels onto the target image using interpolated
    samples from the source image along a line starting at uv1 and ending at
    uv2
  */
  void image_t::blit_hspan(image_t *target, vec2_t p, int c, vec2_t uv0, vec2_t uv1) {
    rect_t b = target->_clip;
    if(p.x < b.x || p.x > b.x + b.w) {
      return;
    }

    fx16_t u = f_to_fx16(uv0.x);
    fx16_t v = f_to_fx16(uv0.y);

    fx16_t ud = f_to_fx16(uv1.x - uv0.x) / c;
    fx16_t vd = f_to_fx16(uv1.y - uv0.y) / c;

    if(p.x < b.x) {
      u += ud * (b.x - p.x);
      v += vd * (b.x - p.x);
      c -= int(b.x - p.x);
      p.x = b.x;
    }

    if(p.x + c > b.x + b.w) {
      c = b.w - p.x;
    }

    uint32_t tw = int(this->_bounds.w - 1);
    uint32_t th = int(this->_bounds.h - 1);

    uint32_t *dst = (uint32_t *)target->ptr(p.x, p.y);
    for(int i = 0; i < c; i++) {
      u += ud;
      v += vd;

      // get fractional part of u, v coordinates and scale to source image
      uint32_t cu = ((u & 0xffffu) * tw) >> 16;
      uint32_t cv = ((v & 0xffffu) * th) >> 16;

      //uint32_t col = *(uint32_t *)this->ptr((u + 32768) >> 16, (v + 32768) >> 16);
      uint32_t col = *(uint32_t *)this->ptr(cu, cv);

      if(this->_has_palette) {
        col = this->_palette[col];
      }

      if(this->_alpha != 255) {
        col = _premul_mul_alpha(col, this->_alpha);
      }

      *dst = target->_blend_func(*dst, _r(col), _g(col), _b(col), _a(col));
      dst++;
    }
  }

  /*
    blits a vertical span of pixels onto the target image using interpolated
    samples from the source image along a line starting at uv1 and ending at
    uv2
  */
  void image_t::blit_vspan(image_t *target, vec2_t p, int c, vec2_t uv0, vec2_t uv1) {
    rect_t b = target->_clip;
    if(p.x < b.x || p.x > b.x + b.w) {
      return;
    }

    fx16_t u = f_to_fx16(uv0.x);
    fx16_t v = f_to_fx16(uv0.y);

    fx16_t ud = f_to_fx16(uv1.x - uv0.x) / c;
    fx16_t vd = f_to_fx16(uv1.y - uv0.y) / c;

    if(p.y < b.y) {
      u += ud * (b.y - p.y);
      v += vd * (b.y - p.y);
      c -= int(b.y - p.y);
      p.y = b.y;
    }

    if(p.y + c > b.y + b.h) {
      c = b.h - p.y;
    }

    uint32_t tw = int(this->_bounds.w - 1);
    uint32_t th = int(this->_bounds.h - 1);

    uint32_t *dst = (uint32_t *)target->ptr(p.x, p.y);

    uint32_t stride = target->_row_stride >> 2;
    for(int i = 0; i < c; i++) {
      u += ud;
      v += vd;

      // get fractional part of u, v coordinates and scale to source image
      uint32_t cu = ((u & 0xffffu) * tw) >> 16;
      uint32_t cv = ((v & 0xffffu) * th) >> 16;

      //uint32_t col = *(uint32_t *)this->ptr((u + 32768) >> 16, (v + 32768) >> 16);
      uint32_t col;

      if(this->_has_palette) {
        col = this->_palette[*(uint8_t*)this->ptr(cu, cv)];
      } else {
        col = *(uint32_t *)this->ptr(cu, cv);
      }

      if(this->_alpha != 255) {
        col = _premul_mul_alpha(col, this->_alpha);
      }

      *dst = target->_blend_func(*dst, _r(col), _g(col), _b(col), _a(col));
      dst += stride;
    }
  }


  void image_t::shape(shape_t *shape) {
    render(shape, this, &shape->transform, _brush);
  }

  void image_t::rectangle(rect_t r) {
    r = r.intersection(_clip);
    span_func_t fn = this->_span_func;
    for(int y = r.y; y < r.y + r.h; y++) {
      fn(this, this->_brush, r.x, y, r.w);
    }
  }

  void image_t::span(int x, int y, int w) {
    if(y < _clip.y || y >= _clip.y + _clip.h) return;
    if(x + w < 0 || x >= _clip.x + _clip.w) return;

    if(x < 0) {
      w += x; x = 0;
    }

    if(x + w >= _clip.x + _clip.w) {
      w = _clip.x + _clip.w - x;
    }
    this->_span_func(this, this->_brush, x, y, w);
  }

  void image_t::masked_span(int x, int y, int w, uint8_t *mask) {
    if(y < _clip.y || y >= _clip.y + _clip.h) return;
    if(x + w < 0 || x >= _clip.x + _clip.w) return;

    if(x < 0) {
      w += x; x = 0;
    }

    if(x + w >= _clip.x + _clip.w) {
      w = _clip.x + _clip.w - x;
    }

    this->_masked_span_func(this, this->_brush, x, y, w, mask);
  }

  void image_t::circle(const vec2_t &p, const int &r) {
    rect_t b = rect_t(p.x - r, p.y - r, r * 2, r * 2);
    if(!b.intersects(_clip)) return;

    int ox = r, oy = 0, err = -r;
    while (ox >= oy)
    {
      int last_oy = oy;

      err += oy; oy++; err += oy;

      this->span(p.x - ox, p.y + last_oy, ox * 2 + 1);
      if (last_oy != 0) {
        this->span(p.x - ox, p.y - last_oy, ox * 2 + 1);
      }

      if(err >= 0 && ox != last_oy) {
        this->span(p.x - last_oy, p.y + ox, last_oy * 2 + 1);
        if (ox != 0) {
          this->span(p.x - last_oy, p.y - ox, last_oy * 2 + 1);
        }

        err -= ox; ox--; err -= ox;
      }
    }
  }

  int32_t orient2d(vec2_t p1, vec2_t p2, vec2_t p3) {
    return (p2.x - p1.x) * (p3.y - p1.y) - (p2.y - p1.y) * (p3.x - p1.x);
  }

  bool is_top_left(const vec2_t &p1, const vec2_t &p2) {
    return (p1.y == p2.y && p1.x > p2.x) || (p1.y < p2.y);
  }

  void image_t::triangle(vec2_t p1, vec2_t p2, vec2_t p3) {
    rect_t b(
      vec2_t(min(p1.x, min(p2.x, p3.x)), min(p1.y, min(p2.y, p3.y))),
      vec2_t(max(p1.x, max(p2.x, p3.x)), max(p1.y, max(p2.y, p3.y)))
    );

    // clip extremes to frame buffer size
    b = b.intersection(_clip);

    // if triangle completely out of bounds then don't bother!
    if (b.empty()) return;

    // fix "winding" of vertices if needed
    int32_t winding = orient2d(p1, p2, p3);
    if (winding < 0) {
      vec2_t t;
      t = p1; p1 = p3; p3 = t;
    }

    // bias ensures no overdraw between neighbouring triangles
    int8_t bias0 = is_top_left(p2, p3) ? 0 : -1;
    int8_t bias1 = is_top_left(p3, p1) ? 0 : -1;
    int8_t bias2 = is_top_left(p1, p2) ? 0 : -1;

    int32_t a01 = p1.y - p2.y;
    int32_t b01 = p2.x - p1.x;
    int32_t a12 = p2.y - p3.y;
    int32_t b12 = p3.x - p2.x;
    int32_t a20 = p3.y - p1.y;
    int32_t b20 = p1.x - p3.x;

    vec2_t tl(b.x, b.y);
    int32_t w0row = orient2d(p2, p3, tl) + bias0;
    int32_t w1row = orient2d(p3, p1, tl) + bias1;
    int32_t w2row = orient2d(p1, p2, tl) + bias2;

    span_func_t fn = this->_span_func;

    for (int32_t y = 0; y < b.h; y++) {
      int32_t w0 = w0row;
      int32_t w1 = w1row;
      int32_t w2 = w2row;

      int xo = b.x;
      int yo = b.y + y;
      for (int32_t x = 0; x < b.w; x++) {
        if ((w0 | w1 | w2) >= 0) {
          fn(this, this->_brush, xo, yo, 1);
        }

        xo++;
        w0 += a12; w1 += a20; w2 += a01;
      }

      w0row += b12; w1row += b20; w2row += b01;

    }
  }

  void round_rectangle(const rect_t &r, int radius) {

  }


  void ellipse(const vec2_t &p, const int &rx, const int &ry) {

  }


  void image_t::line(vec2_t p1, vec2_t p2) {
    rect_t b = this->_clip;
    b.w -= 1;
    b.h -= 1; // TODO: this is hacky... fix it properly
    if(!clip_line(p1, p2, b)) {
      return; // fully outside bounds, nothing to draw
    }

    int x0 = p1.x;
    int x1 = p2.x;
    int y0 = p1.y;
    int y1 = p2.y;

    int dx = abs(x1 - x0);
    int sx = x0 < x1 ? 1 : -1;
    int dy = -abs(y1 - y0);
    int sy = y0 < y1 ? 1 : -1;
    int err = dx + dy;

    span_func_t fn = this->_span_func;

    while(true) {
        fn(this, this->_brush, x0, y0, 1);
        if (x0 == x1 && y0 == y1) break;
        int e2 = 2 * err;
        if (e2 >= dy) {err += dy; x0 += sx;}
        if (e2 <= dx) {err += dx; y0 += sy;}
    }
  }

  void image_t::put(const vec2_t &p) {
    this->put(p.x, p.y);
  }

  void image_t::put(int x, int y) {
    if(x < _clip.x || x >= _clip.x + _clip.w || y < _clip.y || y >= _clip.y + _clip.h) {
      return;
    }
    this->_span_func(this, this->_brush, x, y, 1);
  }

  void image_t::put_unsafe(int x, int y) {
    this->_span_func(this, this->_brush, x, y, 1);
    //this->_brush->render_span(this, x, y, 1);
  }

  uint32_t image_t::get(const vec2_t &p) {
    return this->get(p.x, p.y);
  }

  uint32_t image_t::get(int x, int y) {
    x = max(int(_clip.x), min(x, int(_clip.x + _clip.w - 1)));
    y = max(int(_clip.y), min(y, int(_clip.y + _clip.h - 1)));
    return this->get_unsafe(x, y);
  }

  uint32_t image_t::get_unsafe(int x, int y) {
    if(this->_has_palette) {
      uint8_t pi = *((uint8_t *)ptr(x, y));
      return this->_palette[pi];
    }
    return *((uint32_t *)ptr(x, y));
  }
}