#include "mp_helpers.hpp"
#include "picovector.hpp"

#include "../algorithms/algorithms.hpp"

extern "C" {
  #include "py/runtime.h"

  MPY_BIND_STATICMETHOD_VAR(3, clip_line, {
    vec2_obj_t *p1 = (vec2_obj_t *)MP_OBJ_TO_PTR(args[0]);
    vec2_obj_t *p2 = (vec2_obj_t *)MP_OBJ_TO_PTR(args[1]);
    const rect_obj_t *r = (rect_obj_t *)MP_OBJ_TO_PTR(args[2]);

    bool result = clip_line(p1->v, p2->v, r->r);
    return mp_obj_new_bool(result);
  })

  MPY_BIND_STATICMETHOD_VAR(3, dda, {
    vec2_t point = mp_obj_get_vec2(args[0]);
    float angle = mp_obj_get_float(args[1]);
    float depth = mp_obj_get_float(args[2]);

    mp_obj_t result = mp_obj_new_list(0, NULL);
    vec2_t vector = vec2_t(cosf(angle), sinf(angle));

    dda(point, vector, [&result, &depth](float hit_x, float hit_y, int gx, int gy, int edge, float offset, float distance) -> bool {
      vec2_obj_t *cb_p = mp_obj_malloc(vec2_obj_t, &type_vec2);
      vec2_obj_t *cb_g = mp_obj_malloc(vec2_obj_t, &type_vec2);

      cb_p->v.x = hit_x;
      cb_p->v.y = hit_y;

      cb_g->v.x = gx;
      cb_g->v.y = gy;

      mp_obj_t items[5] = {
        MP_OBJ_FROM_PTR(cb_p),
        MP_OBJ_FROM_PTR(cb_g),
        mp_obj_new_int(edge),
        mp_obj_new_float(offset),
        mp_obj_new_float(distance)
      };

      mp_obj_list_append(result, mp_obj_new_tuple(5, items));

      return distance < depth;
    });


    return result;
  })


  MPY_BIND_STATICMETHOD_VAR(5, raycast, {
    vec2_obj_t *p = (vec2_obj_t *)MP_OBJ_TO_PTR(args[0]);
    float angle = mp_obj_get_float(args[1]);
    float fov = mp_obj_get_float(args[2]);
    int rays = mp_obj_get_int(args[3]);
    int max = mp_obj_get_int(args[4]);


    mp_buffer_info_t map;
    mp_get_buffer_raise(args[5], &map, MP_BUFFER_RW);
    uint8_t *data = (uint8_t *)map.buf;

    int width = mp_obj_get_int(args[6]);
    int height = mp_obj_get_int(args[7]);
    int screen_width = mp_obj_get_int(args[8]);

    mp_obj_t *result = new mp_obj_t[rays];

    float d_proj = (screen_width * 0.5f) / tanf(fov * 0.5f);

    for(int i = 0; i < rays; i++) {
      float x = (i + 0.5f) * (screen_width / (float)rays); // column center in pixels
      float dx = x - screen_width * 0.5f;

      float delta = atanf(dx / d_proj);                // radians
      float ray_ang = angle + delta; // radians

      vec2_t v = vec2_t(cosf(ray_ang), sinf(ray_ang));

      int step = 0;

      mp_obj_t ray = mp_obj_new_list(0, NULL);

      dda(p->v, v, [&step, &data, &width, &ray, &max, &ray_ang, &angle](float hit_x, float hit_y, int gx, int gy, int edge, float offset, float distance) -> bool {
        vec2_obj_t *cb_p = mp_obj_malloc(vec2_obj_t, &type_vec2);
        vec2_obj_t *cb_g = mp_obj_malloc(vec2_obj_t, &type_vec2);

        cb_p->v.x = hit_x;
        cb_p->v.y = hit_y;

        cb_g->v.x = gx;
        cb_g->v.y = gy;

        if(data[(gy * width) + gx] > 0) {
          float perp_distance = distance * cos(ray_ang - angle);

          mp_obj_t items[7] = {
            mp_obj_new_int(data[(gy * width) + gx]),
            MP_OBJ_FROM_PTR(cb_p),
            MP_OBJ_FROM_PTR(cb_g),
            mp_obj_new_int(edge),
            mp_obj_new_float(offset),
            mp_obj_new_float(perp_distance),
            mp_obj_new_float(ray_ang),
          };

          mp_obj_list_append(ray, mp_obj_new_tuple(7, items));

          if(data[(gy * width) + gx] >= 128) {
            return false;
          }
        }

        step++;

        return distance < max;
      });

      result[i] = ray;
    }

    return mp_obj_new_tuple(rays, result);
  })

  MPY_BIND_LOCALS_DICT(algorithm,
    MPY_BIND_ROM_PTR_STATIC(clip_line),
    MPY_BIND_ROM_PTR_STATIC(dda),
    MPY_BIND_ROM_PTR_STATIC(raycast),
  )


  MP_DEFINE_CONST_OBJ_TYPE(
      type_algorithm,
      MP_QSTR_algorithm,
      MP_TYPE_FLAG_NONE,
      locals_dict, &algorithm_locals_dict
  );


}


