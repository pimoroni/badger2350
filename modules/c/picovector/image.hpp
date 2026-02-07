#pragma once

#include <stdint.h>
#include <string>
#include <vector>

#include "picovector.config.hpp"
#include "types.hpp"
#include "blend.hpp"

using std::vector;

namespace picovector {

  class image_t;
  class brush_t;

  // empty implementations for unsupported modes
  void span_func_nop(image_t *target, brush_t *brush, int x, int y, int w);
  void masked_span_func_nop(image_t *target, brush_t *brush, int x, int y, int w, uint8_t *mask);

  typedef void (*span_func_t)(image_t *target, brush_t *brush, int x, int y, int w);
  typedef void (*masked_span_func_t)(image_t *target, brush_t *brush, int x, int y, int w, uint8_t *mask);

  typedef enum antialias_t {
    OFF   = 0,
    LOW   = 1,
    X2    = 1,
    HIGH  = 2,
    X4    = 2
  } antialias_t;

  typedef enum pixel_format_t {
    RGBA8888 = 1,
    RGBA4444 = 2,
  } pixel_format_t;

  typedef std::vector<uint32_t, PV_STD_ALLOCATOR<uint32_t>> palette_t;

  class mat3_t;
  class font_t;
  class pixel_font_t;
  class shape_t;
  class brush_t;

  class image_t {
    friend class brush_t;

    private:
      void              *_buffer = nullptr;
      bool               _managed_buffer = false;
      size_t             _row_stride;
      size_t             _bytes_per_pixel;

      rect_t             _bounds;
      rect_t             _clip;
      uint8_t            _alpha = 255;
      antialias_t        _antialias = OFF;
      pixel_format_t     _pixel_format = RGBA8888;
      bool               _has_palette = false;
      brush_t           *_brush = nullptr;
      font_t            *_font = nullptr;
      pixel_font_t      *_pixel_font = nullptr;
      palette_t          _palette;

    public:
      blend_func_t       _blend_func = blend_func_over;
      span_func_t        _span_func = span_func_nop;
      masked_span_func_t _masked_span_func = masked_span_func_nop;

      image_t();
      image_t(image_t *source, rect_t r);
      image_t(int w, int h, pixel_format_t pixel_format=RGBA8888, bool has_palette=false);
      image_t(void *buffer, int w, int h, pixel_format_t pixel_format=RGBA8888, bool has_palette=false);
      ~image_t();

      size_t buffer_size();
      size_t bytes_per_pixel();
      bool is_compatible(image_t *other);
      void window(image_t *source, rect_t viewport);
      image_t window(rect_t r);
      inline void* ptr(int x, int y) const {
        return (uint8_t *)(this->_buffer) + (x * this->_bytes_per_pixel) + (y * this->_row_stride);
      }
      uint32_t row_stride();

      rect_t bounds();
      rect_t clip();
      void clip(rect_t r);

      bool has_palette();
      // void delete_palette();
      void palette(uint8_t i, uint32_t c);
      uint32_t palette(uint8_t i);

      uint8_t alpha();
      void alpha(uint8_t alpha);

      antialias_t antialias();
      void antialias(antialias_t antialias);

      pixel_format_t pixel_format();
      void pixel_format(pixel_format_t pixel_format);

      brush_t *brush();
      void brush(brush_t *brush);

      font_t *font();
      void font(font_t *font);

      pixel_font_t *pixel_font();
      void pixel_font(pixel_font_t *pixel_font);

      void span(int x, int y, int w);
      void masked_span(int x, int y, int w, uint8_t *mask);


      // raster primitives
      void clear();
      void rectangle(rect_t r);
      void triangle(vec2_t p1, vec2_t p2, vec2_t p3);
      void round_rectangle(const rect_t &r, int radius);
      void circle(const vec2_t &p, const int &r);
      void ellipse(const vec2_t &p, const int &rx, const int &ry);
      void line(vec2_t p1, vec2_t p2);

      // vector shapes
      void shape(shape_t *shape);

      // pixel accessors
      void put(const vec2_t &p1);
      void put(int x, int y);
      void put_unsafe(int x, int y);
      uint32_t get(const vec2_t &p1);
      uint32_t get(int x, int y);
      uint32_t get_unsafe(int x, int y);

      // filters
      void blur(float radius);
      void dither();
      void onebit();
      void monochrome();

      // blitting
      void blit(image_t *t, const vec2_t p);
      void blit(image_t *t, rect_t tr);
      void blit(image_t *t, rect_t sr, rect_t tr);
      void blit_hspan(image_t *target, vec2_t p, int c, vec2_t uv0, vec2_t uv1);
      void blit_vspan(image_t *target, vec2_t p, int c, vec2_t uv0, vec2_t uv1);
  };

}
