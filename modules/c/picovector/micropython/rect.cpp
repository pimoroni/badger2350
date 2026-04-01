#include "mp_tracked_allocator.hpp"

#include "mp_helpers.hpp"
#include "picovector.hpp"

using namespace picovector;

bool mp_obj_is_rect(mp_obj_t rect_in) {
  return mp_obj_is_type(rect_in, &type_rect);
}

rect_t mp_obj_get_rect(mp_obj_t rect_in) {
  if(mp_obj_is_rect(rect_in)) {
    rect_obj_t *rect = (rect_obj_t *)MP_OBJ_TO_PTR(rect_in);
    return rect->r;
  }
  mp_raise_msg_varg(&mp_type_ValueError, MP_ERROR_TEXT("invalid parameters, expected rect(x, y, w, h)"));
}

rect_t mp_obj_get_rect_from_xywh(const mp_obj_t *args) {
    int x = mp_obj_get_float(args[0]);
    int y = mp_obj_get_float(args[1]);
    int w = mp_obj_get_float(args[2]);
    int h = mp_obj_get_float(args[3]);
    return rect_t(x, y, w, h);
}

extern "C" {
  #include "py/runtime.h"

  MPY_BIND_NEW(rect, {
    rect_obj_t *self = mp_obj_malloc_with_finaliser(rect_obj_t, type);

    if(n_args != 4 && n_args != 0) {
      mp_raise_msg_varg(&mp_type_ValueError, MP_ERROR_TEXT("invalid parameters, expected rect() or rect(x, y, w, h)"));
    }

    if(n_args == 4) {
      self->r.x = mp_obj_get_float(args[0]);
      self->r.y = mp_obj_get_float(args[1]);
      self->r.w = mp_obj_get_float(args[2]);
      self->r.h = mp_obj_get_float(args[3]);
    }
    return MP_OBJ_FROM_PTR(self);
  })

  MPY_BIND_VAR(2, deflate, {
    rect_obj_t *self = (rect_obj_t *)MP_OBJ_TO_PTR(args[0]);
    float a1 = mp_obj_get_float(args[1]);
    float a2 = n_args == 3 ? mp_obj_get_float(args[2]) : a1;
    self->r.deflate(a1, a2, a1, a2);
    return mp_const_none;
  })

  MPY_BIND_VAR(2, inflate, {
    rect_obj_t *self = (rect_obj_t *)MP_OBJ_TO_PTR(args[0]);
    float a1 = mp_obj_get_float(args[1]);
    float a2 = n_args == 3 ? mp_obj_get_float(args[2]) : a1;
    self->r.inflate(a1, a2, a1, a2);
    return mp_const_none;
  })

  MPY_BIND_CLASSMETHOD_ARGS1(intersection, rect_in, {
    rect_obj_t *self = (rect_obj_t *)MP_OBJ_TO_PTR(self_in);
    rect_obj_t *other = (rect_obj_t *)MP_OBJ_TO_PTR(rect_in);
    rect_obj_t *result = mp_obj_malloc(rect_obj_t, &type_rect);
    result->r = self->r.intersection(other->r);
    return MP_OBJ_FROM_PTR(result);
  })

  MPY_BIND_CLASSMETHOD_ARGS1(intersects, rect_in, {
    rect_obj_t *self = (rect_obj_t *)MP_OBJ_TO_PTR(self_in);
    rect_obj_t *other = (rect_obj_t *)MP_OBJ_TO_PTR(rect_in);
    rect_obj_t *result = mp_obj_malloc(rect_obj_t, &type_rect);
    return mp_obj_new_bool(self->r.intersects(other->r));
  })

  MPY_BIND_CLASSMETHOD_ARGS1(contains, obj_in, {
    rect_obj_t *self = (rect_obj_t *)MP_OBJ_TO_PTR(self_in);

    if(mp_obj_is_type(obj_in, &type_rect)) {
      rect_obj_t *other = (rect_obj_t *)MP_OBJ_TO_PTR(obj_in);
      return mp_obj_new_bool(self->r.contains(other->r));
    }

    if(mp_obj_is_type(obj_in, &type_vec2)) {
      vec2_obj_t *vec2 = (vec2_obj_t *)MP_OBJ_TO_PTR(obj_in);
      return mp_obj_new_bool(self->r.contains(vec2->v));
    }

    mp_raise_msg_varg(&mp_type_ValueError, MP_ERROR_TEXT("invalid parameters, expected either rect(x, y, w, h) or vec2(x, y)"));

    return mp_const_none;
  })

  MPY_BIND_VAR(2, offset, {
    rect_obj_t *self = (rect_obj_t *)MP_OBJ_TO_PTR(args[0]);

    if(n_args == 3) {
      float xo = mp_obj_get_float(args[1]);
      float yo = mp_obj_get_float(args[2]);
      self->r.offset(xo, yo);
      return mp_const_none;
    }

    if(mp_obj_is_type(args[1], &type_vec2)) {
      vec2_obj_t *vec2 = (vec2_obj_t *)MP_OBJ_TO_PTR(args[1]);
      self->r.offset(vec2->v);
      return mp_const_none;
    }

    mp_raise_msg_varg(&mp_type_ValueError, MP_ERROR_TEXT("invalid parameters, expected either offset(p) or offset(x, y)"));
  })

  MPY_BIND_CLASSMETHOD_ARGS0(empty, {
    rect_obj_t *self = (rect_obj_t *)MP_OBJ_TO_PTR(self_in);
    return mp_obj_new_bool(self->r.empty());
  })

  MPY_BIND_ATTR(rect, {
    self(self_in, rect_obj_t);

    action_t action = m_attr_action(dest);

    switch(attr | action) {
      case MP_QSTR_l | GET:
      case MP_QSTR_x | GET:
        dest[0] = mp_obj_new_float(self->r.x);
        return;

      case MP_QSTR_l | SET:
      case MP_QSTR_x | SET:
        self->r.x = mp_obj_get_float(dest[1]);
        dest[0] = MP_OBJ_NULL;
        return;

      case MP_QSTR_t | GET:
      case MP_QSTR_y | GET:
        dest[0] = mp_obj_new_float(self->r.y);
        return;

      case MP_QSTR_t | SET:
      case MP_QSTR_y | SET:
        self->r.y = mp_obj_get_float(dest[1]);
        dest[0] = MP_OBJ_NULL;
        return;

      case MP_QSTR_w | GET:
        dest[0] = mp_obj_new_float(self->r.w);
        return;

      case MP_QSTR_w | SET:
        self->r.w = mp_obj_get_float(dest[1]);
        dest[0] = MP_OBJ_NULL;
        return;

      case MP_QSTR_h | GET:
        dest[0] = mp_obj_new_float(self->r.h);
        return;

      case MP_QSTR_h | SET:
        self->r.h = mp_obj_get_float(dest[1]);
        dest[0] = MP_OBJ_NULL;
        return;

      case MP_QSTR_r | GET:
        dest[0] = mp_obj_new_float(self->r.w + self->r.x);
        return;

      case MP_QSTR_r | SET:
        self->r.w = mp_obj_get_float(dest[1]) - self->r.x;
        dest[0] = MP_OBJ_NULL;
        return;

      case MP_QSTR_b | GET:
        dest[0] = mp_obj_new_float(self->r.h + self->r.y);
        return;

      case MP_QSTR_b | SET:
        self->r.h = mp_obj_get_float(dest[1]) - self->r.y;
        dest[0] = MP_OBJ_NULL;
        return;
    };

    dest[1] = MP_OBJ_SENTINEL;
  })


  static void rect_print(const mp_print_t *print, mp_obj_t self_in, mp_print_kind_t kind) {
    self(self_in, rect_obj_t);
    mp_printf(print, "rect(%f, %f -> %f x %f)", self->r.x, self->r.y, self->r.w, self->r.h);
  }

  MPY_BIND_LOCALS_DICT(rect,
    MPY_BIND_ROM_PTR(deflate),
    MPY_BIND_ROM_PTR(inflate),
    MPY_BIND_ROM_PTR(intersection),
    MPY_BIND_ROM_PTR(intersects),
    MPY_BIND_ROM_PTR(contains),
    MPY_BIND_ROM_PTR(empty),
    MPY_BIND_ROM_PTR(offset),
  )

  MP_DEFINE_CONST_OBJ_TYPE(
      type_rect,
      MP_QSTR_rect,
      MP_TYPE_FLAG_NONE,
      make_new, (const void *)rect_new,
      print, (const void *)rect_print,
      attr, (const void *)rect_attr,
      locals_dict, &rect_locals_dict
  );

}


