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

  static inline int jpegdec_decode(image_obj_t &target, JPEGDEC *jpeg) {
    if(target.image == nullptr) {
      printf("jpeg decode, new image_t(%d, %d)\n", jpeg->getWidth(), jpeg->getHeight());
      target.image = new(m_malloc(sizeof(image_t))) image_t(jpeg->getWidth(), jpeg->getHeight(), RGBA8888, false);
    }

    jpeg->setUserPointer((void *)target.image);
    jpeg->setPixelType(RGB888_LITTLE_ENDIAN);

    int status = jpeg->decode(0, 0, 0);
    jpeg->close();
    return status ? JPEG_SUCCESS : JPEG_DECODE_ERROR;
  }

  int jpegdec_open_ram(image_obj_t &target, const void* buffer, const size_t size) {
    JPEGDEC *jpeg = new(PicoVector_working_buffer) JPEGDEC();
    int status = jpeg->openRAM((uint8_t *)buffer, size, jpegdec_decode_callback);
    if (status != 1) {
      return JPEG_INVALID_FILE;
    }
    return jpegdec_decode(target, jpeg);
  }

  int jpegdec_open_file(image_obj_t &target, const char *path) {
    JPEGDEC *jpeg = new(PicoVector_working_buffer) JPEGDEC();
    int status = jpeg->open(path, jpegdec_open_callback, jpegdec_close_callback, jpegdec_read_callback, jpegdec_seek_callback, jpegdec_decode_callback);
    if (status != 1) {
      return JPEG_INVALID_FILE;
    }
    return jpegdec_decode(target, jpeg);
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
    image_t *target = (image_t *)pDraw->pUser;
    uint8_t *pixels = (uint8_t *)pDraw->pPixels;
    for(int y = 0; y < pDraw->iHeight; y++) {
        for(int x = 0; x < pDraw->iWidth; x++) {
            if(x >= pDraw->iWidthUsed) break; // Clip to the used width
            int offset = (y * pDraw->iWidth + x) * 3;
            uint8_t r = pixels[offset];
            uint8_t g = pixels[offset + 1];
            uint8_t b = pixels[offset + 2];
            uint32_t *pdst = (uint32_t *)target->ptr(pDraw->x + x, pDraw->y + y);
            *pdst = rgb_color_t(r, g, b, 255)._p;
        }
    }
    return 1;
}

}