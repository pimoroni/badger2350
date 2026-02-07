#include "mp_tracked_allocator.hpp"

#include "mp_helpers.hpp"
#include "picovector.hpp"
#include "../blend.hpp"

extern "C" {

  #include "py/runtime.h"

  MPY_BIND_STATICMETHOD_VAR(3, rgb, {
    int r = (int)mp_obj_get_float(args[0]);
    int g = (int)mp_obj_get_float(args[1]);
    int b = (int)mp_obj_get_float(args[2]);
    int a = n_args > 3 ? (int)mp_obj_get_float(args[3]) : 255;
    color_obj_t *color = mp_obj_malloc(color_obj_t, &type_color);
    color->c = new rgb_color_t(r, g, b, a);
    return MP_OBJ_FROM_PTR(color);
  })

  MPY_BIND_STATICMETHOD_VAR(3, hsv, {
    int h = (int)mp_obj_get_float(args[0]);
    h = fmod(h, 360.0f);
    int s = (int)mp_obj_get_float(args[1]);
    int v = (int)mp_obj_get_float(args[2]);
    int a = n_args > 3 ? (int)mp_obj_get_float(args[3]) : 255;
    color_obj_t *color = mp_obj_malloc(color_obj_t, &type_color);
    color->c = new hsv_color_t(h, s, v, a);
    return MP_OBJ_FROM_PTR(color);
  })

  MPY_BIND_STATICMETHOD_VAR(3, oklch, {
    int l = (int)mp_obj_get_float(args[0]);
    int c = (int)mp_obj_get_float(args[1]);
    int h = (int)mp_obj_get_float(args[2]);
    int a = n_args > 3 ? (int)mp_obj_get_float(args[3]) : 255;
    color_obj_t *color = mp_obj_malloc(color_obj_t, &type_color);
    color->c = new oklch_color_t(l, c, h, a);
    return MP_OBJ_FROM_PTR(color);
  })

  MPY_BIND_VAR(2, blend, {
    const color_obj_t *self = (color_obj_t *)MP_OBJ_TO_PTR(args[0]);
    const color_obj_t *other = (color_obj_t *)MP_OBJ_TO_PTR(args[1]);
    uint8_t *src = (uint8_t*)&other->c;
    color_obj_t *result = mp_obj_malloc(color_obj_t, &type_color);
    result->c = self->c;
    // blend_func_over(uint32_t dst, uint32_t r, uint32_t g, uint32_t b, uint32_t a)

    // blend_rgba_rgba((uint8_t*)&result->c, src[0], src[1], src[2], src[3]);
    return MP_OBJ_FROM_PTR(result);
  })

  // static inline uint8_t darken_u8(uint8_t c, uint8_t factor) {
  //   return (uint8_t)((c * factor) >> 8);
  // }

  MPY_BIND_VAR(2, darken, {
    const color_obj_t *self = (color_obj_t *)MP_OBJ_TO_PTR(args[0]);
    int v = 255 - (int)mp_obj_get_float(args[1]);
    color_obj_t *result = mp_obj_malloc(color_obj_t, &type_color);
    result->c = self->c;
    // set_r(&result->c, darken_u8(get_r(&self->c), v));
    // set_g(&result->c, darken_u8(get_g(&self->c), v));
    // set_b(&result->c, darken_u8(get_b(&self->c), v));
    // TODO: fix
    return MP_OBJ_FROM_PTR(result);
  })

  // static inline uint8_t lighten_u8(uint8_t c, uint factor) {
  //   // factor >= 256 (1.0x)
  //   uint16_t v = (c * factor) >> 8;
  //   return v > 255 ? 255 : (uint8_t)v;
  // }

  MPY_BIND_VAR(2, lighten, {
    const color_obj_t *self = (color_obj_t *)MP_OBJ_TO_PTR(args[0]);
    int v = 256 + (int)mp_obj_get_float(args[1]);
    color_obj_t *result = mp_obj_malloc(color_obj_t, &type_color);
    result->c = self->c;
    // set_r(&result->c, lighten_u8(get_r(&self->c), v));
    // set_g(&result->c, lighten_u8(get_g(&self->c), v));
    // set_b(&result->c, lighten_u8(get_b(&self->c), v));
    // TODO: fix
    return MP_OBJ_FROM_PTR(result);
  })

  static void attr(mp_obj_t self_in, qstr attr, mp_obj_t *dest) {
    self(self_in, color_obj_t);

    action_t action = m_attr_action(dest);

    constexpr size_t GET = 0b1 << 31;
    constexpr size_t SET = 0b1 << 30;
    constexpr size_t DELETE = 0b1 << 29;

    switch(attr | action) {
      case MP_QSTR_p | GET:
        dest[0] = mp_obj_new_int(self->c->_p);
        return;

      // case MP_QSTR_r | GET:
      //   dest[0] = mp_obj_new_int(get_r(&self->c));
      //   return;

      // case MP_QSTR_r | SET:
      //   set_r(&self->c, (int)mp_obj_get_float(dest[1]));
      //   dest[0] = MP_OBJ_NULL;
      //   return;

      // case MP_QSTR_g | GET:
      //   dest[0] = mp_obj_new_int(get_g(&self->c));
      //   return;

      // case MP_QSTR_g | SET:
      //   set_g(&self->c, (int)mp_obj_get_float(dest[1]));
      //   dest[0] = MP_OBJ_NULL;
      //   return;

      // case MP_QSTR_b | GET:
      //   dest[0] = mp_obj_new_int(get_b(&self->c));
      //   return;

      // case MP_QSTR_b | SET:
      //   set_b(&self->c, (int)mp_obj_get_float(dest[1]));
      //   dest[0] = MP_OBJ_NULL;
      //   return;

      // case MP_QSTR_a | GET:
      //   dest[0] = mp_obj_new_int(get_a(&self->c));
      //   return;

      // case MP_QSTR_a | SET:
      //   set_a(&self->c, (int)mp_obj_get_float(dest[1]));
      //   dest[0] = MP_OBJ_NULL;
      //   return;

      // case MP_QSTR_raw | GET:
      //   dest[0] = mp_obj_new_int(self->c);
      //   return;

      // case MP_QSTR_raw | SET:
      //   self->c = mp_obj_get_int(dest[1]);
      //   dest[0] = MP_OBJ_NULL;
      //   return;
    };

    dest[1] = MP_OBJ_SENTINEL;
  }

  // static void color_print(const mp_print_t *print, mp_obj_t self_in, mp_print_kind_t kind) {
  //   self(self_in, color_obj_t);

  //   if(self->c.a() == 255) {
  //     mp_printf(print, "color(r=%d, g=%d, b=%d)", self->c.r(), self->c.g(), self->c.b());
  //   }else{
  //     mp_printf(print, "color(r=%d, g=%d, b=%d, a=%d)", self->c.r(), self->c.g(), self->c.b(), self->c.a());
  //   }
  // }

#ifdef TUFTY
  rgb_color_t _color_black  = rgb_color_t(0x14, 0x1e, 0x28, 0xff);
  rgb_color_t _color_white  = rgb_color_t(0xde, 0xee, 0xd6, 0xff);
#else
  rgb_color_t _color_black  = rgb_color_t(0x00, 0x00, 0x00, 0xff);
  rgb_color_t _color_white  = rgb_color_t(0xff, 0xff, 0xff, 0xff);
#endif

  rgb_color_t _color_grape  = rgb_color_t(0x44, 0x24, 0x34, 0xff);
  rgb_color_t _color_navy   = rgb_color_t(0x30, 0x34, 0x6d, 0xff);
  rgb_color_t _color_grey   = rgb_color_t(0x4e, 0x4a, 0x4e, 0xff);
  rgb_color_t _color_brown  = rgb_color_t(0x85, 0x4c, 0x30, 0xff);
  rgb_color_t _color_green  = rgb_color_t(0x34, 0x65, 0x24, 0xff);
  rgb_color_t _color_red    = rgb_color_t(0xd0, 0x46, 0x48, 0xff);
  rgb_color_t _color_taupe  = rgb_color_t(0x75, 0x71, 0x61, 0xff);
  rgb_color_t _color_blue   = rgb_color_t(0x59, 0x7d, 0xce, 0xff);
  rgb_color_t _color_orange = rgb_color_t(0xd2, 0x7d, 0x2c, 0xff);
  rgb_color_t _color_smoke  = rgb_color_t(0x85, 0x95, 0xa1, 0xff);
  rgb_color_t _color_lime   = rgb_color_t(0x6d, 0xaa, 0x2c, 0xff);
  rgb_color_t _color_latte  = rgb_color_t(0xd2, 0xaa, 0x99, 0xff);
  rgb_color_t _color_cyan   = rgb_color_t(0x6d, 0xc2, 0xca, 0xff);
  rgb_color_t _color_yellow = rgb_color_t(0xda, 0xd4, 0x5e, 0xff);
  rgb_color_t _color_transparent  = rgb_color_t(0x00, 0x00, 0x00, 0x00);

  // default palette based on Dawnbringer 16
  const color_obj_t color_black_obj  = {.base = {.type = &type_color}, .c = &_color_black};
  const color_obj_t color_grape_obj  = {.base = {.type = &type_color}, .c = &_color_grape};
  const color_obj_t color_navy_obj   = {.base = {.type = &type_color}, .c = &_color_navy};
  const color_obj_t color_grey_obj   = {.base = {.type = &type_color}, .c = &_color_grey};
  const color_obj_t color_brown_obj  = {.base = {.type = &type_color}, .c = &_color_brown};
  const color_obj_t color_green_obj  = {.base = {.type = &type_color}, .c = &_color_green};
  const color_obj_t color_red_obj    = {.base = {.type = &type_color}, .c = &_color_red};
  const color_obj_t color_taupe_obj  = {.base = {.type = &type_color}, .c = &_color_taupe};
  const color_obj_t color_blue_obj   = {.base = {.type = &type_color}, .c = &_color_blue};
  const color_obj_t color_orange_obj = {.base = {.type = &type_color}, .c = &_color_orange};
  const color_obj_t color_smoke_obj  = {.base = {.type = &type_color}, .c = &_color_smoke};
  const color_obj_t color_lime_obj   = {.base = {.type = &type_color}, .c = &_color_lime};
  const color_obj_t color_latte_obj  = {.base = {.type = &type_color}, .c = &_color_latte};
  const color_obj_t color_cyan_obj   = {.base = {.type = &type_color}, .c = &_color_cyan};
  const color_obj_t color_yellow_obj = {.base = {.type = &type_color}, .c = &_color_yellow};
  const color_obj_t color_white_obj  = {.base = {.type = &type_color}, .c = &_color_white};
  const color_obj_t color_transparent_obj  = {.base = {.type = &type_color}, .c = &_color_transparent};

  // badger E-ink specific greys
  rgb_color_t _color_light_grey = rgb_color_t(0xc0, 0xc0, 0xc0, 0xff);
  rgb_color_t _color_dark_grey  = rgb_color_t(0x40, 0x40, 0x40, 0xff);

  const color_obj_t color_light_grey_obj  = {.base = {.type = &type_color}, .c = &_color_light_grey};
  const color_obj_t color_dark_grey_obj   = {.base = {.type = &type_color}, .c = &_color_dark_grey};

  MPY_BIND_LOCALS_DICT(color,
    // static color generators
    MPY_BIND_ROM_PTR_STATIC(rgb),
    MPY_BIND_ROM_PTR_STATIC(hsv),
    MPY_BIND_ROM_PTR_STATIC(oklch),

    // color modifiers
    MPY_BIND_ROM_PTR(darken),
    MPY_BIND_ROM_PTR(lighten),
    MPY_BIND_ROM_PTR(blend),

    { MP_ROM_QSTR(MP_QSTR_black),  MP_ROM_PTR(&color_black_obj) },
    { MP_ROM_QSTR(MP_QSTR_grape),  MP_ROM_PTR(&color_grape_obj) },
    { MP_ROM_QSTR(MP_QSTR_navy),   MP_ROM_PTR(&color_navy_obj) },
    { MP_ROM_QSTR(MP_QSTR_grey),   MP_ROM_PTR(&color_grey_obj) },
    { MP_ROM_QSTR(MP_QSTR_brown),  MP_ROM_PTR(&color_brown_obj) },
    { MP_ROM_QSTR(MP_QSTR_green),  MP_ROM_PTR(&color_green_obj) },
    { MP_ROM_QSTR(MP_QSTR_red),    MP_ROM_PTR(&color_red_obj) },
    { MP_ROM_QSTR(MP_QSTR_taupe),  MP_ROM_PTR(&color_taupe_obj) },
    { MP_ROM_QSTR(MP_QSTR_blue),   MP_ROM_PTR(&color_blue_obj) },
    { MP_ROM_QSTR(MP_QSTR_orange), MP_ROM_PTR(&color_orange_obj) },
    { MP_ROM_QSTR(MP_QSTR_smoke),  MP_ROM_PTR(&color_smoke_obj) },
    { MP_ROM_QSTR(MP_QSTR_lime),   MP_ROM_PTR(&color_lime_obj) },
    { MP_ROM_QSTR(MP_QSTR_latte),  MP_ROM_PTR(&color_latte_obj) },
    { MP_ROM_QSTR(MP_QSTR_cyan),   MP_ROM_PTR(&color_cyan_obj) },
    { MP_ROM_QSTR(MP_QSTR_yellow), MP_ROM_PTR(&color_yellow_obj) },
    { MP_ROM_QSTR(MP_QSTR_white),  MP_ROM_PTR(&color_white_obj) },
    { MP_ROM_QSTR(MP_QSTR_transparent),  MP_ROM_PTR(&color_transparent_obj) },

    // badger E-ink specific greys
    { MP_ROM_QSTR(MP_QSTR_light_grey),  MP_ROM_PTR(&color_light_grey_obj) },
    { MP_ROM_QSTR(MP_QSTR_dark_grey),  MP_ROM_PTR(&color_dark_grey_obj) },
  )

  MP_DEFINE_CONST_OBJ_TYPE(
      type_color,
      MP_QSTR_color,
      MP_TYPE_FLAG_NONE,
      //print, (const void *)color_print,
      attr, (const void *)attr,
      locals_dict, &color_locals_dict
  );
}