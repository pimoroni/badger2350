#include "mp_helpers.hpp"
#include "picovector.hpp"

extern "C" {

  #include "py/stream.h"
  #include "py/reader.h"
  #include "py/runtime.h"
  #include "extmod/vfs.h"

  #ifndef NO_QSTR
    #include "PNGdec.h"
  #endif

  static void *pngdec_open_callback(const char *filename, int32_t *size);
  static void pngdec_close_callback(void *handle);
  static int32_t pngdec_read_callback(PNGFILE *png, uint8_t *p, int32_t c);
  static int32_t pngdec_seek_callback(PNGFILE *png, int32_t p);
  static void pngdec_decode_callback(PNGDRAW *pDraw);

  struct pngdec_decode_data_t {
    fx16_t step_x;
    fx16_t step_y;
    fx16_t cur_y;
    bool set_palette = false;
    image_t* image;
  };

  static inline int pngdec_decode(image_obj_t &target, PNG *png, int target_width, int target_height) {
    pngdec_decode_data_t decode_data;

    int width = png->getWidth();
    int height = png->getHeight();

    if (target.image != nullptr) {
      rect_t bounds = target.image->bounds();
      target_width = bounds.w;
      target_height = bounds.h;
    }

    if (target_width > width) target_width = width;
    if (target_height > height) target_height = height;

    if(target.image == nullptr) {
      if (target_width == 0 && target_height == 0) {
        target_width = width;
        target_height = height;
      }
      else if (target_width != 0 && target_height == 0) {
        target_height = (height * ((target_width << 16) / width)) >> 16;
      }
      else if (target_height != 0 && target_width == 0) {
        target_width = (width * ((target_height << 16) / height)) >> 16;
      }

      bool has_palette = png->getPixelType() == PNG_PIXEL_INDEXED;

      target.image = new(m_malloc(sizeof(image_t))) image_t(target_width, target_height, RGBA8888, has_palette);
    }

    decode_data.image = target.image;
    decode_data.step_x = f_to_fx16((float)target_width / (float)width);
    decode_data.step_y = f_to_fx16((float)target_height / (float)height);
    decode_data.cur_y = -decode_data.step_y;

    int status = png->decode((void *)&decode_data, 0);
    png->close();
    return status;
  }

  int pngdec_open_ram(image_obj_t &target, const void* buffer, const size_t size, int target_width, int target_height) {
    PNG *png = new(PicoVector_working_buffer) PNG();
    int status = png->openRAM((uint8_t *)buffer, size, pngdec_decode_callback);
    if (status != PNG_SUCCESS) {
      return status;
    }
    return pngdec_decode(target, png, target_width, target_height);
  }

  int pngdec_open_file(image_obj_t &target, const char *path, int target_width, int target_height) {
    PNG *png = new(PicoVector_working_buffer) PNG();
    int status = png->open(path, pngdec_open_callback, pngdec_close_callback, pngdec_read_callback, pngdec_seek_callback, pngdec_decode_callback);
    if (status != PNG_SUCCESS) {
      return status;
    }
    return pngdec_decode(target, png, target_width, target_height);
  }

  static void *pngdec_open_callback(const char *filename, int32_t *size) {
    mp_obj_t fn = mp_obj_new_str(filename, (mp_uint_t)strlen(filename));

    mp_obj_t args[2] = {
        fn,
        MP_ROM_QSTR(MP_QSTR_r),
    };

    // Stat the file to get its size
    // example tuple response: (32768, 0, 0, 0, 0, 0, 5153, 1654709815, 1654709815, 1654709815)
    mp_obj_t stat = mp_vfs_stat(fn);
    mp_obj_tuple_t *tuple = (mp_obj_tuple_t*)MP_OBJ_TO_PTR(stat);
    *size = mp_obj_get_int(tuple->items[6]);

    png_handle_t *png_handle = (png_handle_t *)m_tracked_calloc(1, sizeof(png_handle_t));
    png_handle->fhandle = mp_vfs_open(MP_ARRAY_SIZE(args), &args[0], (mp_map_t *)&mp_const_empty_map);

    return (void *)png_handle;
  }

  static void pngdec_close_callback(void *handle) {
    png_handle_t *png_handle = (png_handle_t *)(handle);
    mp_stream_close(png_handle->fhandle);
    m_tracked_free(handle);
  }

  static int32_t pngdec_read_callback(PNGFILE *png, uint8_t *p, int32_t c) {
    png_handle_t *png_handle = (png_handle_t *)(png->fHandle);
    int error;
    return mp_stream_read_exactly(png_handle->fhandle, p, c, &error);
  }

  // Re-implementation of stream.c/static mp_obj_t stream_seek(size_t n_args, const mp_obj_t *args)
  static int32_t pngdec_seek_callback(PNGFILE *png, int32_t p) {
    png_handle_t *png_handle = (png_handle_t *)(png->fHandle);
    struct mp_stream_seek_t seek_s;
    seek_s.offset = p;
    seek_s.whence = SEEK_SET;

    const mp_stream_p_t *stream_p = mp_get_stream(png_handle->fhandle);

    int error;
    mp_uint_t res = stream_p->ioctl(png_handle->fhandle, MP_STREAM_SEEK, (mp_uint_t)(uintptr_t)&seek_s, &error);
    if (res == MP_STREAM_ERROR) {
        mp_raise_msg_varg(&mp_type_OSError, MP_ERROR_TEXT("PNG: seek failed with %d"), error);
    }

    return seek_s.offset;
  }

  static void pngdec_decode_callback(PNGDRAW *pDraw) {
    pngdec_decode_data_t* decode_data = (pngdec_decode_data_t*)pDraw->pUser;

    fx16_t last_y = decode_data->cur_y >> 16;
    decode_data->cur_y += decode_data->step_y;
    if (decode_data->cur_y >> 16 == last_y) {
      return;
    }

    image_t *target = decode_data->image;
    uint8_t *pixels = (uint8_t *)pDraw->pPixels;

    uint8_t *psrc = (uint8_t *)pDraw->pPixels;
    int w = pDraw->iWidth;

    fx16_t cur_x = 0;

    switch(pDraw->iPixelType) {
      case PNG_PIXEL_TRUECOLOR: {
        uint32_t *pdst = (uint32_t *)target->ptr(0, decode_data->cur_y >> 16);
        while(w--) {
          rgb_color_t c(psrc[0], psrc[1], psrc[2], 255);
          *pdst = c._p;
          pdst++;

          fx16_t last_x = cur_x >> 16;
          do {
            psrc += 3;
            cur_x += decode_data->step_x;
          } while (cur_x >> 16 == last_x);          
        }
      } break;

      case PNG_PIXEL_TRUECOLOR_ALPHA: {
        uint32_t *pdst = (uint32_t *)target->ptr(0, decode_data->cur_y >> 16);
        while(w--) {
          rgb_color_t c(psrc[0], psrc[1], psrc[2], psrc[3]);
          *pdst = c._p;
          pdst++;

          fx16_t last_x = cur_x >> 16;
          do {
            psrc += 4;
            cur_x += decode_data->step_x;
          } while (cur_x >> 16 == last_x);
        }
      } break;

      case PNG_PIXEL_INDEXED: {
        if(target->has_palette()) {
          if (!decode_data->set_palette) {
            for(int i = 0; i < 256; i++) {
              rgb_color_t c(
                pDraw->pPalette[i * 3 + 0],
                pDraw->pPalette[i * 3 + 1],
                pDraw->pPalette[i * 3 + 2],
                pDraw->iHasAlpha ? pDraw->pPalette[768 + i] : 255
              );
              target->palette(i, c._p);
            }
            decode_data->set_palette = true;
          }

          uint8_t *pdst = (uint8_t *)target->ptr(0, decode_data->cur_y >> 16);
          while(w--) {
            *pdst = *psrc;
            pdst++;

            fx16_t last_x = cur_x >> 16;
            do {
              psrc++;
              cur_x += decode_data->step_x;
            } while (cur_x >> 16 == last_x);
          }
        } else {
          uint32_t *pdst = (uint32_t *)target->ptr(0, decode_data->cur_y >> 16);
          while(w--) {
            *pdst = rgb_color_t(
              pDraw->pPalette[*psrc * 3 + 0],
              pDraw->pPalette[*psrc * 3 + 1],
              pDraw->pPalette[*psrc * 3 + 2],
              pDraw->iHasAlpha ? pDraw->pPalette[768 + *psrc] : 255
            )._p;
            pdst++;

            fx16_t last_x = cur_x >> 16;
            do {
              psrc++;
              cur_x += decode_data->step_x;
            } while (cur_x >> 16 == last_x);
          }
        }
      } break;
      case PNG_PIXEL_GRAYSCALE: {
        uint32_t *pdst = (uint32_t *)target->ptr(0, decode_data->cur_y >> 16);
        while(w--) {
          uint8_t src = *psrc;
          // do something with index here
          switch(pDraw->iBpp) {
            case 8: {
              *pdst = rgb_color_t(src, src, src, 255)._p;
              pdst++;
            } break;

            case 4: {
              int src1 = (src & 0xf0) | ((src & 0xf0) >> 4);
              int src2 = (src & 0x0f) | ((src & 0x0f) << 4);
              *pdst = rgb_color_t(src1, src1, src1, 255)._p;
              pdst++;
              *pdst = rgb_color_t(src2, src2, src2, 255)._p;
              pdst++;
            } break;

            case 1: {
              for(uint8_t mask = 0b10000000; mask < 0; mask >>= 1) {
                int v = (src & mask) ? 255 : 0;
                *pdst++ = rgb_color_t(v, v, v, 255)._p;
              }
            } break;
          }

          fx16_t last_x = cur_x >> 16;
          do {
            psrc++;
            cur_x += decode_data->step_x;
          } while (cur_x >> 16 == last_x);
        }
      } break;

      default: {
        // TODO: raise file not supported error
      } break;
    }
  }
}