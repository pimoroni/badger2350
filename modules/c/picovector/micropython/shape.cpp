#include "mp_helpers.hpp"
#include "picovector.hpp"

extern "C" {

  #include "py/runtime.h"

  mp_obj_t shape__del__(mp_obj_t self_in) {
    self(self_in, shape_obj_t);
    m_del_class(shape_t, self->shape);
    return mp_const_none;
  }
  static MP_DEFINE_CONST_FUN_OBJ_1(shape__del___obj, shape__del__);

  MPY_BIND_STATICMETHOD_VAR(1, custom, {
    shape_obj_t *shape = mp_obj_malloc_with_finaliser(shape_obj_t, &type_shape);

    size_t path_count = n_args;
    shape->shape = new(PV_MALLOC(sizeof(shape_t))) shape_t(path_count);

    for (size_t i = 0; i < path_count; i++) {
      if(!mp_obj_is_type(args[i], &mp_type_list)) {
        mp_raise_msg_varg(&mp_type_TypeError, MP_ERROR_TEXT("invalid parameter, expected custom([p1, p2, p3, ...], ...)"));
      }

      size_t points_count;
      mp_obj_t *points;
      mp_obj_list_get(args[i], &points_count, &points);

      path_t poly(points_count);
      for(size_t i = 0; i < points_count; i++) {
        if(!mp_obj_is_type(points[i], &type_vec2)) {
          mp_raise_msg_varg(&mp_type_TypeError, MP_ERROR_TEXT("invalid parameter, expected custom([p1, p2, p3, ...])"));
        }
        const vec2_obj_t *point = (vec2_obj_t *)MP_OBJ_TO_PTR(points[i]);
        poly.add_point(point->v);
      }
      shape->shape->add_path(poly);
    }

    return MP_OBJ_FROM_PTR(shape);
  })

  MPY_BIND_STATICMETHOD_VAR(4, regular_polygon, {
    float x = mp_obj_get_float(args[0]);
    float y = mp_obj_get_float(args[1]);
    float r = mp_obj_get_float(args[2]);
    int s = mp_obj_get_float(args[3]);
    shape_obj_t *shape = mp_obj_malloc_with_finaliser(shape_obj_t, &type_shape);
    shape->shape = regular_polygon(x, y, s, r);
    return MP_OBJ_FROM_PTR(shape);
  })

  MPY_BIND_STATICMETHOD_VAR(2, circle, {
    float x;
    float y;
    float r;

    if(n_args == 3) {
      x = mp_obj_get_float(args[0]);
      y = mp_obj_get_float(args[1]);
      r = mp_obj_get_float(args[2]);
    } else if (n_args == 2 && mp_obj_is_type(args[0], &type_vec2)) {
      const vec2_obj_t *point = (vec2_obj_t *)MP_OBJ_TO_PTR(args[0]);
      x = point->v.x;
      y = point->v.y;
      r = mp_obj_get_float(args[1]);
    } else {
      mp_raise_msg_varg(&mp_type_ValueError, MP_ERROR_TEXT("invalid parameters, expected either circle(p, r) or circle(x, y, r)"));
    }

    shape_obj_t *shape = mp_obj_malloc_with_finaliser(shape_obj_t, &type_shape);
    shape->shape = circle(x, y, r);
    return MP_OBJ_FROM_PTR(shape);
  })

  MPY_BIND_STATICMETHOD_VAR(1, rectangle, {
    float x;
    float y;
    float w;
    float h;

    if(n_args == 4) {
      x = mp_obj_get_float(args[0]);
      y = mp_obj_get_float(args[1]);
      w = mp_obj_get_float(args[2]);
      h = mp_obj_get_float(args[3]);
    } else if (n_args == 1 && mp_obj_is_type(args[0], &type_rect)) {
      const rect_t *rect = (rect_t *)MP_OBJ_TO_PTR(args[0]);
      x = rect->x;
      y = rect->y;
      w = rect->w;
      h = rect->h;
    } else {
      mp_raise_msg_varg(&mp_type_ValueError, MP_ERROR_TEXT("invalid parameters, expected either rectangle(rect) or rectangle(x, y, w, h)"));
    }

    shape_obj_t *shape = mp_obj_malloc_with_finaliser(shape_obj_t, &type_shape);
    shape->shape = rectangle(x, y, w, h);
    return MP_OBJ_FROM_PTR(shape);
  })

  MPY_BIND_STATICMETHOD_VAR(5, rounded_rectangle, {
    float x = mp_obj_get_float(args[0]);
    float y = mp_obj_get_float(args[1]);
    float w = mp_obj_get_float(args[2]);
    float h = mp_obj_get_float(args[3]);
    float r1 = mp_obj_get_float(args[4]);
    float r2 = r1;
    float r3 = r1;
    float r4 = r1;
    if(n_args >= 6) { r2 = mp_obj_get_float(args[5]); }
    if(n_args >= 7) { r3 = mp_obj_get_float(args[6]); }
    if(n_args >= 8) { r4 = mp_obj_get_float(args[7]); }

    shape_obj_t *shape = mp_obj_malloc_with_finaliser(shape_obj_t, &type_shape);
    shape->shape = rounded_rectangle(x, y, w, h, r1, r2, r3, r4);
    return MP_OBJ_FROM_PTR(shape);
  })

  MPY_BIND_STATICMETHOD_VAR(3, squircle, {
    float x = mp_obj_get_float(args[0]);
    float y = mp_obj_get_float(args[1]);
    float s = mp_obj_get_float(args[2]);
    float n = 4.0f;
    if(n_args == 4) {
      n = mp_obj_get_float(args[3]);
      n = max(2.0f, n);
      n = max(2.0f, n);
    }
    shape_obj_t *shape = mp_obj_malloc_with_finaliser(shape_obj_t, &type_shape);
    shape->shape = squircle(x, y, s, n);
    return MP_OBJ_FROM_PTR(shape);
  })

  MPY_BIND_STATICMETHOD_VAR(6, arc, {
    float x = mp_obj_get_float(args[0]);
    float y = mp_obj_get_float(args[1]);
    float i = mp_obj_get_float(args[2]);
    float o = mp_obj_get_float(args[3]);
    float f = mp_obj_get_float(args[4]);
    float t = mp_obj_get_float(args[5]);
    shape_obj_t *shape = mp_obj_malloc_with_finaliser(shape_obj_t, &type_shape);
    shape->shape = arc(x, y, f, t, i, o);
    return MP_OBJ_FROM_PTR(shape);
  })

  MPY_BIND_STATICMETHOD_VAR(5, pie, {
    float x = mp_obj_get_float(args[0]);
    float y = mp_obj_get_float(args[1]);
    float r = mp_obj_get_float(args[2]);
    float f = mp_obj_get_float(args[3]);
    float t = mp_obj_get_float(args[4]);
    shape_obj_t *shape = mp_obj_malloc_with_finaliser(shape_obj_t, &type_shape);
    shape->shape = pie(x, y, f, t, r);
    return MP_OBJ_FROM_PTR(shape);
  })

  MPY_BIND_STATICMETHOD_VAR(5, star, {
    float x = mp_obj_get_float(args[0]);
    float y = mp_obj_get_float(args[1]);
    int s = mp_obj_get_float(args[2]);
    float ro = mp_obj_get_float(args[3]);
    float ri = mp_obj_get_float(args[4]);
    shape_obj_t *shape = mp_obj_malloc_with_finaliser(shape_obj_t, &type_shape);
    shape->shape = star(x, y, s, ro, ri);
    return MP_OBJ_FROM_PTR(shape);
  })

  MPY_BIND_STATICMETHOD_VAR(5, line, {
    float x1 = mp_obj_get_float(args[0]);
    float y1 = mp_obj_get_float(args[1]);
    float x2 = mp_obj_get_float(args[2]);
    float y2 = mp_obj_get_float(args[3]);
    float w = mp_obj_get_float(args[4]);
    shape_obj_t *shape = mp_obj_malloc_with_finaliser(shape_obj_t, &type_shape);
    shape->shape = line(x1, y1, x2, y2, w);
    return MP_OBJ_FROM_PTR(shape);
  })

  MPY_BIND_VAR(1, stroke, {
    const shape_obj_t *self = (shape_obj_t *)MP_OBJ_TO_PTR(args[0]);
    float width = mp_obj_get_float(args[1]);
    self->shape->stroke(width);
    return MP_OBJ_FROM_PTR(self);
  })

  static void shape_attr(mp_obj_t self_in, qstr attr, mp_obj_t *dest) {
    self(self_in, shape_obj_t);

    action_t action = m_attr_action(dest);

    switch(attr) {
      case MP_QSTR_transform: {
        if(action == GET) {
          mat3_obj_t *out = mp_obj_malloc_with_finaliser(mat3_obj_t, &type_mat3);
          out->m = self->shape->transform;
          dest[0] = MP_OBJ_FROM_PTR(out);
          return;
        }

        if(action == SET) {
          if(!mp_obj_is_type(dest[1], &type_mat3)) {
            mp_raise_TypeError(MP_ERROR_TEXT("expected mat3"));
          }
          mat3_obj_t *in = (mat3_obj_t *)MP_OBJ_TO_PTR(dest[1]);
          self->shape->transform = in->m;
          dest[0] = MP_OBJ_NULL;
          return;
        }
      };
    }

    dest[1] = MP_OBJ_SENTINEL;
  }

  /*
    micropython bindings
  */

  MPY_BIND_LOCALS_DICT(shape,
    { MP_ROM_QSTR(MP_QSTR___del__), MP_ROM_PTR(&shape__del___obj) },
    MPY_BIND_ROM_PTR(stroke),
    MPY_BIND_ROM_PTR_STATIC(custom),
    MPY_BIND_ROM_PTR_STATIC(regular_polygon),
    MPY_BIND_ROM_PTR_STATIC(squircle),
    MPY_BIND_ROM_PTR_STATIC(circle),
    MPY_BIND_ROM_PTR_STATIC(rectangle),
    MPY_BIND_ROM_PTR_STATIC(rounded_rectangle),
    MPY_BIND_ROM_PTR_STATIC(arc),
    MPY_BIND_ROM_PTR_STATIC(pie),
    MPY_BIND_ROM_PTR_STATIC(star),
    MPY_BIND_ROM_PTR_STATIC(line),
  )

  MP_DEFINE_CONST_OBJ_TYPE(
      type_shape,
      MP_QSTR_shape,
      MP_TYPE_FLAG_NONE,
      attr, (const void *)shape_attr,
      locals_dict, &shape_locals_dict
  );


}
