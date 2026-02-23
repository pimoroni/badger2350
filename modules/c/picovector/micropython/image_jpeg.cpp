#include "mp_helpers.hpp"
#include "picovector.hpp"

extern "C" {

  #include "py/stream.h"
  #include "py/reader.h"
  #include "py/runtime.h"
  #include "extmod/vfs.h"

  #ifndef NO_QSTR
    #include "JPEGDEC.h"
  #endif

  static void *jpegdec_open_callback(const char *filename, int32_t *size);
  static void jpegdec_close_callback(void *handle);
  static int32_t jpegdec_read_callback(JPEGFILE *jpeg, uint8_t *p, int32_t c);
  static int32_t jpegdec_seek_callback(JPEGFILE *jpeg, int32_t p);
  static int jpegdec_decode_callback(JPEGDRAW *pDraw);

  struct jpecdec_decode_data_t {
    float x_ratio;
    float y_ratio;
    image_t* image;
  };

  static inline int jpegdec_decode(image_obj_t &target, JPEGDEC *jpeg, int target_width, int target_height) {
    int scale = 1;
    jpecdec_decode_data_t decode_data;

    int width = jpeg->getWidth();
    int height = jpeg->getHeight();

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

      // Use JPEG scaling if image is much larger than target
      while (width > target_width << 1 && height > target_height << 1 && scale < 8) {
        scale <<= 1;
        width >>= 1;
        height >>= 1;
      }

      target.image = new(m_malloc(sizeof(image_t))) image_t(target_width, target_height, RGBA8888, false);
    }

    decode_data.image = target.image;
    decode_data.x_ratio = (float)target_width / (float)width;
    decode_data.y_ratio = (float)target_height / (float)height;

    jpeg->setUserPointer((void *)&decode_data);
    jpeg->setPixelType(RGB888_LITTLE_ENDIAN);

    int jpeg_options = 0;
    if (scale > 1) jpeg_options = scale;
    int status = jpeg->decode(0, 0, jpeg_options);
    jpeg->close();
    return status ? JPEG_SUCCESS : JPEG_DECODE_ERROR;
  }

  int jpegdec_open_ram(image_obj_t &target, const void* buffer, const size_t size, int target_width, int target_height) {
    JPEGDEC *jpeg = new(PicoVector_working_buffer) JPEGDEC();
    int status = jpeg->openRAM((uint8_t *)buffer, size, jpegdec_decode_callback);
    if (status != 1) {
      return JPEG_INVALID_FILE;
    }
    return jpegdec_decode(target, jpeg, target_width, target_height);
  }

  int jpegdec_open_file(image_obj_t &target, const char *path, int target_width, int target_height) {
    JPEGDEC *jpeg = new(PicoVector_working_buffer) JPEGDEC();
    int status = jpeg->open(path, jpegdec_open_callback, jpegdec_close_callback, jpegdec_read_callback, jpegdec_seek_callback, jpegdec_decode_callback);
    if (status != 1) {
      return JPEG_INVALID_FILE;
    }
    return jpegdec_decode(target, jpeg, target_width, target_height);
  }

  static void *jpegdec_open_callback(const char *filename, int32_t *size) {
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

    jpeg_handle_t *jpeg_handle = (jpeg_handle_t *)m_tracked_calloc(1, sizeof(jpeg_handle_t));
    jpeg_handle->fhandle = mp_vfs_open(MP_ARRAY_SIZE(args), &args[0], (mp_map_t *)&mp_const_empty_map);

    return (void *)jpeg_handle;
  }

  static void jpegdec_close_callback(void *handle) {
    jpeg_handle_t *jpeg_handle = (jpeg_handle_t *)(handle);
    mp_stream_close(jpeg_handle->fhandle);
    m_tracked_free(handle);
  }

  static int32_t jpegdec_read_callback(JPEGFILE *jpeg, uint8_t *p, int32_t c) {
    jpeg_handle_t *jpeg_handle = (jpeg_handle_t *)(jpeg->fHandle);
    int error;
    return mp_stream_read_exactly(jpeg_handle->fhandle, p, c, &error);
  }

  // Re-implementation of stream.c/static mp_obj_t stream_seek(size_t n_args, const mp_obj_t *args)
  static int32_t jpegdec_seek_callback(JPEGFILE *jpeg, int32_t p) {
    jpeg_handle_t *jpeg_handle = (jpeg_handle_t *)(jpeg->fHandle);
    struct mp_stream_seek_t seek_s;
    seek_s.offset = p;
    seek_s.whence = SEEK_SET;

    const mp_stream_p_t *stream_p = mp_get_stream(jpeg_handle->fhandle);

    int error;
    mp_uint_t res = stream_p->ioctl(jpeg_handle->fhandle, MP_STREAM_SEEK, (mp_uint_t)(uintptr_t)&seek_s, &error);
    if (res == MP_STREAM_ERROR) {
        mp_raise_msg_varg(&mp_type_OSError, MP_ERROR_TEXT("PNG: seek failed with %d"), error);
    }

    return seek_s.offset;
  }

  static int jpegdec_decode_callback(JPEGDRAW *pDraw) {
    jpecdec_decode_data_t* decode_data = (jpecdec_decode_data_t*)pDraw->pUser;
    image_t *target = decode_data->image;
    uint8_t *pixels = (uint8_t *)pDraw->pPixels;

    fx16_t cur_y = f_to_fx16(decode_data->y_ratio * pDraw->y);
    fx16_t step_x = f_to_fx16(decode_data->x_ratio);
    fx16_t step_y = f_to_fx16(decode_data->y_ratio);

    int y = 0;
    
    while (y < pDraw->iHeight) {
      int x = 0;
      fx16_t cur_x = f_to_fx16(decode_data->x_ratio * pDraw->x);

      uint32_t *pdst = (uint32_t *)target->ptr(cur_x >> 16, cur_y >> 16);
      
      while (x < pDraw->iWidth) {
        if(x >= pDraw->iWidthUsed) break; // Clip to the used width
        int offset = (y * pDraw->iWidth + x) * 3;
        uint8_t r = pixels[offset];
        uint8_t g = pixels[offset + 1];
        uint8_t b = pixels[offset + 2];
        *pdst++ = rgb_color_t(r, g, b, 255)._p;

        // Assume that scaling has got us close to target resolution, so it's not
        // worth doing divisions to avoid these loops.
        fx16_t last_x = cur_x >> 16;
        do {
          ++x;
          cur_x += step_x;
        } while (cur_x >> 16 == last_x);
      }

      fx16_t last_y = cur_y >> 16;
      do {
        ++y;
        cur_y += step_y;
      } while (cur_y >> 16 == last_y);
    }
    return 1;
  }

}