#include "mp_helpers.hpp"
#include "picovector.hpp"

extern "C" {
  #include "py/runtime.h"

  /*MPY_BIND_DEL(brush, {
    self(self_in, brush_obj_t);
    m_del_class(brush_t, self->brush);
    return mp_const_none;
  })*/


  // MPY_BIND_STATICMETHOD_VAR(3, xor, {
  //   int r = mp_obj_get_float(args[0]);
  //   int g = mp_obj_get_float(args[1]);
  //   int b = mp_obj_get_float(args[2]);
  //   brush_obj_t *brush = mp_obj_malloc(brush_obj_t, &type_brush);
  //   //brush->brush = m_new_class(xor_brush, _make_col(r, g, b));
  //   return MP_OBJ_FROM_PTR(brush);
  // })


  // MPY_BIND_STATICMETHOD_VAR(1, brighten, {
  //   int amount = mp_obj_get_float(args[0]);
  //   brush_obj_t *brush = mp_obj_malloc(brush_obj_t, &type_brush);
  //   //brush->brush = m_new_class(brighten_brush, amount);
  //   return MP_OBJ_FROM_PTR(brush);
  // })


  MPY_BIND_STATICMETHOD_VAR(3, pattern, {
    if(!mp_obj_is_type(args[0], &type_color) ||
       !mp_obj_is_type(args[1], &type_color)) {
      mp_raise_msg_varg(&mp_type_TypeError, MP_ERROR_TEXT("invalid parameter, expected brush.pattern(color, color, index | tuple[8], [on=image])"));
    }

    const color_obj_t *c1 = (color_obj_t *)MP_OBJ_TO_PTR(args[0]);
    const color_obj_t *c2 = (color_obj_t *)MP_OBJ_TO_PTR(args[1]);

    brush_obj_t *brush = mp_obj_malloc(brush_obj_t, &type_brush);
    if(mp_obj_is_int(args[2])) { // brush index supplied, use pre-baked brush
      int pattern_index = mp_obj_get_int(args[2]);
      if(pattern_index < 0 || pattern_index > 37) {
        mp_raise_TypeError(MP_ERROR_TEXT("invalid parameter, pattern index must be a number between 0 and 37"));
      }
      brush->brush = m_new_class(pattern_brush_t, *c1->c, *c2->c, pattern_index);
    }else if(mp_obj_is_type(args[2], &mp_type_tuple)) { // custom pattern passed as tuple
      size_t len;
      mp_obj_t *items;
      mp_obj_get_array(args[2], &len, &items);

      if(len != 8) {
        mp_raise_TypeError(MP_ERROR_TEXT("invalid parameter, custom pattern must be a tuple with 8 elements"));
      }
      uint8_t pattern[8];
      for(int i = 0; i < 8; i++) {
        pattern[i] = mp_obj_get_int(items[i]);
      }
      brush->brush = m_new_class(pattern_brush_t, *c1->c, *c2->c, pattern);
    } else {
      mp_raise_msg_varg(&mp_type_TypeError, MP_ERROR_TEXT("invalid parameter, expected brush.pattern(color, color, index | tuple[8], [on=image])"));
    }

    return MP_OBJ_FROM_PTR(brush);
  })


  MPY_BIND_STATICMETHOD_VAR(1, image, {
    if(!mp_obj_is_type(args[0], &type_image) ||
       (n_args >= 1 && !mp_obj_is_type(args[1], &type_mat3))) {
      mp_raise_msg_varg(&mp_type_TypeError, MP_ERROR_TEXT("invalid parameter, expected brush.image(image, [mat3], [on=image])"));
    }
    brush_obj_t *brush = mp_obj_malloc(brush_obj_t, &type_brush);
    const image_obj_t *src = (image_obj_t *)MP_OBJ_TO_PTR(args[0]);

    if(n_args == 1) {
      brush->brush = m_new_class(image_brush_t, src->image);
    } else {
      mat3_obj_t *transform = (mat3_obj_t *)MP_OBJ_TO_PTR(args[1]);
      mat3_t *m = &transform->m;
      brush->brush = m_new_class(image_brush_t, src->image, m);
    }

    return MP_OBJ_FROM_PTR(brush);
  })


  MPY_BIND_LOCALS_DICT(brush,
    // MPY_BIND_ROM_PTR_DEL(brush),
    // MPY_BIND_ROM_PTR_STATIC(xor),
    // MPY_BIND_ROM_PTR_STATIC(brighten),
    MPY_BIND_ROM_PTR_STATIC(pattern),
    MPY_BIND_ROM_PTR_STATIC(image),
  )


  MP_DEFINE_CONST_OBJ_TYPE(
      type_brush,
      MP_QSTR_brush,
      MP_TYPE_FLAG_NONE,
      locals_dict, &brush_locals_dict
  );


}
