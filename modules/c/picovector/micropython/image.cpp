#include "mp_helpers.hpp"
#include "picovector.hpp"

extern "C" {

  #include "py/stream.h"
  #include "py/reader.h"
  #include "py/runtime.h"
  #include "py/objstr.h"


  mp_obj_t image__del__(mp_obj_t self_in) {
    self(self_in, image_obj_t);
    if(self->image) {
      //self->image->delete_palette();
      m_del_class(image_t, self->image);
    }
    return mp_const_none;
  }
  static MP_DEFINE_CONST_FUN_OBJ_1(image__del___obj, image__del__);

MPY_BIND_NEW(image, {
    image_obj_t *self = mp_obj_malloc_with_finaliser(image_obj_t, type);

    int w = mp_obj_get_int(args[0]);
    int h = mp_obj_get_int(args[1]);

    if (n_args > 2) {
      mp_buffer_info_t bufinfo;
      mp_get_buffer_raise(args[2], &bufinfo, MP_BUFFER_WRITE);
      self->image = new(m_malloc(sizeof(image_t))) image_t(bufinfo.buf, w, h);
    } else {
      self->image = new(m_malloc(sizeof(image_t))) image_t(w, h);
    }

    return MP_OBJ_FROM_PTR(self);
})

void image_open_helper(image_obj_t &target, mp_obj_t path_or_bytes_in) {
  int status = 0;
  if(mp_obj_is_str(path_or_bytes_in)) {
    const char *path = mp_obj_str_get_str(path_or_bytes_in);
    status = pngdec_open_file(target, path);
    if(status != PNG_SUCCESS) {
      status = jpegdec_open_file(target, path);
    }
  } else {
    mp_buffer_info_t buf;
    mp_get_buffer_raise(path_or_bytes_in, &buf, MP_BUFFER_READ);
    status = pngdec_open_ram(target, buf.buf, buf.len);
    if(status != PNG_SUCCESS) {
      status = jpegdec_open_ram(target, buf.buf, buf.len);
    }
  }
  if(status != 0) {
    mp_raise_msg_varg(&mp_type_ValueError, MP_ERROR_TEXT("unable to read image! %d"), status);
  }
}

MPY_BIND_STATICMETHOD_ARGS1(load, path_or_bytes_in, {
    image_obj_t *result = mp_obj_malloc_with_finaliser(image_obj_t, &type_image);
    result->image = nullptr;
    image_open_helper(*result, path_or_bytes_in);
    return MP_OBJ_FROM_PTR(result);
  })

MPY_BIND_CLASSMETHOD_ARGS1(load_into, path_or_bytes_in, {
    self(self_in, image_obj_t);
    image_open_helper(*self, path_or_bytes_in);
    return mp_const_none;
  })


MPY_BIND_VAR(2, window, {
    const image_obj_t *self = (image_obj_t *)MP_OBJ_TO_PTR(args[0]);

    int x;
    int y;
    int w;
    int h;

    if (mp_obj_is_type(args[1], &type_rect)) {
      const rect_obj_t *rect = (rect_obj_t *)MP_OBJ_TO_PTR(args[1]);
      x = rect->r.x;
      y = rect->r.y;
      w = rect->r.w;
      h = rect->r.h;
    }else{
      x = mp_obj_get_float(args[1]);
      y = mp_obj_get_float(args[2]);
      w = mp_obj_get_float(args[3]);
      h = mp_obj_get_float(args[4]);
    }

    image_obj_t *result = mp_obj_malloc_with_finaliser(image_obj_t, &type_image);
    result->image = new(m_malloc(sizeof(image_t))) image_t(self->image, rect_t(x, y, w, h));
    result->parent = (void*)self;
    return MP_OBJ_FROM_PTR(result);
  })

  MPY_BIND_VAR(2, shape, {
    const image_obj_t *self = (image_obj_t *)MP_OBJ_TO_PTR(args[0]);

    if (mp_obj_is_type(args[1], &type_shape)) {
      const shape_obj_t *shape = (shape_obj_t *)MP_OBJ_TO_PTR(args[1]);
      self->image->shape(shape->shape);
      return mp_const_none;
    }

    if (mp_obj_is_type(args[1], &mp_type_list)) {
      size_t len;
      mp_obj_t *items;
      mp_obj_list_get(args[1], &len, &items);
      for(size_t i = 0; i < len; i++) {
        const shape_obj_t *shape = (shape_obj_t *)MP_OBJ_TO_PTR(items[i]);
        self->image->shape(shape->shape);
      }
      return mp_const_none;
    }

    mp_raise_msg_varg(&mp_type_ValueError, MP_ERROR_TEXT("invalid parameters, expected either shape(s) or shape([s1, s2, s3, ...])"));
  })


  MPY_BIND_VAR(2, rectangle, {
    const image_obj_t *self = (image_obj_t *)MP_OBJ_TO_PTR(args[0]);

    if(mp_obj_is_rect(args[1])) {
      self->image->rectangle(mp_obj_get_rect(args[1]));
      return mp_const_none;
    }

    if(n_args == 5) {
      self->image->rectangle(mp_obj_get_rect_from_xywh(&args[1]));
      return mp_const_none;
    }

    mp_raise_msg_varg(&mp_type_ValueError, MP_ERROR_TEXT("invalid parameters, expected either rectangle(r) or rectangle(x, y, w, h)"));
  })

  MPY_BIND_VAR(3, line, {
    const image_obj_t *self = (image_obj_t *)MP_OBJ_TO_PTR(args[0]);

    if(n_args == 3 && mp_obj_is_vec2(args[1]) && mp_obj_is_vec2(args[2])) {
      vec2_t p1 = mp_obj_get_vec2(args[1]);
      vec2_t p2 = mp_obj_get_vec2(args[2]);
      self->image->line(p1, p2);
      return mp_const_none;
    }

    if(n_args == 5) {
      int x1 = mp_obj_get_float(args[1]);
      int y1 = mp_obj_get_float(args[2]);
      int x2 = mp_obj_get_float(args[3]);
      int y2 = mp_obj_get_float(args[4]);
      self->image->line(vec2_t(x1, y1), vec2_t(x2, y2));
      return mp_const_none;
    }

    mp_raise_msg_varg(&mp_type_ValueError, MP_ERROR_TEXT("invalid parameters, expected either line(p1, p2) or line(x1, y1, x2, y2)"));
  })


  MPY_BIND_VAR(3, circle, {
    const image_obj_t *self = (image_obj_t *)MP_OBJ_TO_PTR(args[0]);

    if(mp_obj_is_vec2(args[1])) {
      vec2_t p = mp_obj_get_vec2(args[1]);
      float r = mp_obj_get_float(args[2]);
      self->image->circle(p, r);
      return mp_const_none;
    }

    if(n_args == 4) {
      int x = mp_obj_get_float(args[1]);
      int y = mp_obj_get_float(args[2]);
      int r = mp_obj_get_float(args[3]);
      self->image->circle(vec2_t(x, y), r);
      return mp_const_none;
    }

    mp_raise_msg_varg(&mp_type_ValueError, MP_ERROR_TEXT("invalid parameters, expected either circle(p, r) or circle(x, y, r)"));
  })

  MPY_BIND_VAR(4, triangle, {
    const image_obj_t *self = (image_obj_t *)MP_OBJ_TO_PTR(args[0]);

    if(n_args == 4 && mp_obj_is_vec2(args[1]) && mp_obj_is_vec2(args[2]) && mp_obj_is_vec2(args[3])) {
      vec2_t p1 = mp_obj_get_vec2(args[1]);
      vec2_t p2 = mp_obj_get_vec2(args[2]);
      vec2_t p3 = mp_obj_get_vec2(args[3]);
      self->image->triangle(p1, p2, p3);
      return mp_const_none;
    }

    if(n_args == 7) {
      vec2_t p1 = mp_obj_get_vec2_from_xy(&args[1]);
      vec2_t p2 = mp_obj_get_vec2_from_xy(&args[3]);
      vec2_t p3 = mp_obj_get_vec2_from_xy(&args[5]);
      self->image->triangle(p1, p2, p3);
      return mp_const_none;
    }

    mp_raise_msg_varg(&mp_type_ValueError, MP_ERROR_TEXT("invalid parameters, expected either triangle(p1, p2, p3) or triangle(x1, y1, x2, y2, x3, y3)"));
  })


MPY_BIND_VAR(2, blur, {
    const image_obj_t *self = (image_obj_t *)MP_OBJ_TO_PTR(args[0]);
    float radius = mp_obj_get_float(args[1]);
    self->image->blur(radius);
    return mp_const_none;
  })


MPY_BIND_VAR(1, dither, {
    const image_obj_t *self = (image_obj_t *)MP_OBJ_TO_PTR(args[0]);
    self->image->dither();
    return mp_const_none;
  })


MPY_BIND_VAR(1, onebit, {
    const image_obj_t *self = (image_obj_t *)MP_OBJ_TO_PTR(args[0]);
    self->image->onebit();
    return mp_const_none;
  })


MPY_BIND_VAR(1, monochrome, {
    const image_obj_t *self = (image_obj_t *)MP_OBJ_TO_PTR(args[0]);
    self->image->monochrome();
    return mp_const_none;
  })

// do we want to allow this with premultiplied alpha?
// would we undo the multiply and return rgba?
MPY_BIND_VAR(2, get, {
    const image_obj_t *self = (image_obj_t *)MP_OBJ_TO_PTR(args[0]);
    vec2_t point;
    if(mp_obj_is_vec2(args[1])) {
      point = mp_obj_get_vec2(args[1]);
    } else {
      point = mp_obj_get_vec2_from_xy(&args[1]);
    }
    color_obj_t *color = mp_obj_malloc(color_obj_t, &type_color);
    uint32_t c = self->image->get(point.x, point.y);
    color->c = new rgb_color_t(_r(c), _g(c), _b(c), _a(c));
    return MP_OBJ_FROM_PTR(color);
  })

MPY_BIND_VAR(2, put, {
    const image_obj_t *self = (image_obj_t *)MP_OBJ_TO_PTR(args[0]);
    vec2_t point;
    if(mp_obj_is_vec2(args[1])) {
      point = mp_obj_get_vec2(args[1]);
    } else {
      point = mp_obj_get_vec2_from_xy(&args[1]);
    }
    self->image->put(point.x, point.y);
    return mp_const_none;
  })

MPY_BIND_VAR(3, text, {
    const image_obj_t *self = (image_obj_t *)MP_OBJ_TO_PTR(args[0]);
    const char *text = mp_obj_str_get_str(args[1]);

    if(!self->font && !self->pixel_font) {
      mp_raise_msg_varg(&mp_type_OSError, MP_ERROR_TEXT("target image has no font"));
    }

    vec2_t point;
    int arg_offset;

    if(mp_obj_is_vec2(args[2])) {
      point = mp_obj_get_vec2(args[2]);
      arg_offset = 3;
    } else {
      point = mp_obj_get_vec2_from_xy(&args[2]);
      arg_offset = 4;
    }

    if(self->font) {
      float size = mp_obj_get_float(args[arg_offset]);
      self->image->font()->draw(self->image, text, point.x, point.y, size);
    }

    if(self->pixel_font) {
      self->image->pixel_font()->draw(self->image, text, point.x, point.y);
    }

    return mp_const_none;
  })

MPY_BIND_VAR(2, measure_text, {
    const image_obj_t *self = (image_obj_t *)MP_OBJ_TO_PTR(args[0]);
    const char *text = mp_obj_str_get_str(args[1]);

    if(!self->font && !self->pixel_font) {
      mp_raise_msg_varg(&mp_type_OSError, MP_ERROR_TEXT("target image has no font"));
    }

    mp_obj_t result[2];

    if(self->font) {
      float size = mp_obj_get_float(args[2]);
      rect_t r = self->image->font()->measure(self->image, text, size);
      result[0] = mp_obj_new_float(r.w);
      result[1] = mp_obj_new_float(r.h);
    }

    if(self->pixel_font) {
      rect_t r = self->image->pixel_font()->measure(self->image, text);
      result[0] = mp_obj_new_float(r.w);
      result[1] = mp_obj_new_float(r.h);
    }

    return mp_obj_new_tuple(2, result);
  })

  // MPY_BIND_VAR(2, shape, {
  //   const image_obj_t *self = (image_obj_t *)MP_OBJ_TO_PTR(args[0]);

  //   if (mp_obj_is_type(args[1], &type_shape)) {
  //     const shape_obj_t *shape = (shape_obj_t *)MP_OBJ_TO_PTR(args[1]);
  //     self->image->shape(shape->shape);
  //     return mp_const_none;
  //   }

  //   if (mp_obj_is_type(args[1], &mp_type_list)) {
  //     size_t len;
  //     mp_obj_t *items;
  //     mp_obj_list_get(args[1], &len, &items);
  //     for(size_t i = 0; i < len; i++) {
  //       const shape_obj_t *shape = (shape_obj_t *)MP_OBJ_TO_PTR(items[i]);
  //       self->image->shape(shape->shape);
  //     }
  //     return mp_const_none;
  //   }

  //   mp_raise_msg_varg(&mp_type_ValueError, MP_ERROR_TEXT("invalid parameters, expected either shape(s) or shape([s1, s2, s3, ...])"));
  // })


  MPY_BIND_VAR(6, blit_vspan, {
    const image_obj_t *self = (image_obj_t *)MP_OBJ_TO_PTR(args[0]);
    const image_obj_t *src = (image_obj_t *)MP_OBJ_TO_PTR(args[1]);

    vec2_t p; // position on screen to start rendering span
    int c; // height of span
    vec2_t uv0; // start uv coordinate
    vec2_t uv1; // end uv coordinate

    if(n_args == 6) {
      p = mp_obj_get_vec2(args[2]);
      c = mp_obj_get_float(args[3]);
      uv0 = mp_obj_get_vec2(args[4]);
      uv1 = mp_obj_get_vec2(args[5]);
    } else if(n_args == 9) {
      p.x = mp_obj_get_float(args[2]);
      p.y = mp_obj_get_float(args[3]);
      c = mp_obj_get_float(args[4]);
      uv0.x = mp_obj_get_float(args[5]);
      uv0.y = mp_obj_get_float(args[6]);
      uv1.x = mp_obj_get_float(args[7]);
      uv1.y = mp_obj_get_float(args[8]);
    } else {
      mp_raise_msg_varg(&mp_type_ValueError, MP_ERROR_TEXT("invalid parameters, expected either blit_vspan(p, c, uvs, uve) or blit_vspan(x, y, x, uvsx, uvsy, uvex, uvey)"));
    }

    src->image->blit_vspan(self->image, p, c, uv0, uv1);

    return mp_const_none;
  })

  MPY_BIND_VAR(6, blit_hspan, {
    const image_obj_t *self = (image_obj_t *)MP_OBJ_TO_PTR(args[0]);
    const image_obj_t *src = (image_obj_t *)MP_OBJ_TO_PTR(args[1]);

    vec2_t p; // position on screen to start rendering span
    int c; // height of span
    vec2_t uvs; // start uv coordinate
    vec2_t uve; // end uv coordinate

    if(n_args == 6) {
      p = mp_obj_get_vec2(args[2]);
      c = mp_obj_get_float(args[3]);
      uvs = mp_obj_get_vec2(args[4]);
      uve = mp_obj_get_vec2(args[5]);
    } else if(n_args == 9) {
      p.x = mp_obj_get_float(args[2]);
      p.y = mp_obj_get_float(args[3]);
      c = mp_obj_get_float(args[4]);
      uvs.x = mp_obj_get_float(args[5]);
      uvs.y = mp_obj_get_float(args[6]);
      uve.x = mp_obj_get_float(args[7]);
      uve.y = mp_obj_get_float(args[8]);
    } else {
      mp_raise_msg_varg(&mp_type_ValueError, MP_ERROR_TEXT("invalid parameters, expected either blit_hspan(p, c, uvs, uve) or blit_hspan(x, y, x, uvsx, uvsy, uvex, uvey)"));
    }

    src->image->blit_hspan(self->image, p, c, uvs, uve);

    return mp_const_none;
  })

MPY_BIND_VAR(3, blit, {
    const image_obj_t *self = (image_obj_t *)MP_OBJ_TO_PTR(args[0]);

    if(mp_obj_is_type(args[1], &type_image)) {

      const image_obj_t *src = (image_obj_t *)MP_OBJ_TO_PTR(args[1]);

      if(n_args == 3 && mp_obj_is_vec2(args[2])) {
        src->image->blit(self->image, mp_obj_get_vec2(args[2]));
        return mp_const_none;
      }

      if(n_args == 4 && mp_obj_is_float(args[2]) && mp_obj_is_float(args[3])) {
        vec2_t p = mp_obj_get_vec2_from_xy(&args[2]);
        src->image->blit(self->image, p);
        return mp_const_none;
      }

      if(n_args == 3 && mp_obj_is_rect(args[2])) {
        src->image->blit(self->image, mp_obj_get_rect(args[2]));
        return mp_const_none;
      }

      if(n_args == 4 && mp_obj_is_rect(args[2]) && mp_obj_is_rect(args[3])) {
        src->image->blit(self->image, mp_obj_get_rect(args[2]), mp_obj_get_rect(args[3]));
        return mp_const_none;
      }

    }

    mp_raise_msg_varg(&mp_type_TypeError, MP_ERROR_TEXT("invalid parameter, expected blit(image, point), blit(image, rect) or blit(image, source_rect, dest_rect)"));
  })

MPY_BIND_VAR(1, clear, {
    const image_obj_t *self = (image_obj_t *)MP_OBJ_TO_PTR(args[0]);
    self->image->clear();
    return mp_const_none;
  })

MPY_BIND_ATTR(image, {
    self(self_in, image_obj_t);

    action_t action = m_attr_action(dest);

    switch(attr) {
      case MP_QSTR_raw: {
        if(action == GET) {
          mp_obj_t raw = mp_obj_new_bytearray_by_ref(self->image->buffer_size(), self->image->ptr(0, 0));
          dest[0] = raw;
          return;
        }
      };

      case MP_QSTR_clip: {
        if(action == GET) {
          rect_obj_t *result = mp_obj_malloc(rect_obj_t, &type_rect);
          result->r = self->image->clip();
          dest[0] = MP_OBJ_FROM_PTR(result);
          return;
        }

        if(action == SET) {
          if(!mp_obj_is_type(dest[1], &type_rect)) {
            mp_raise_TypeError(MP_ERROR_TEXT("value must be of type rect"));
          }

          rect_obj_t * r = (rect_obj_t *)dest[1];
          self->image->clip(r->r);
          dest[0] = MP_OBJ_NULL;
          return;
        }
      };

      case MP_QSTR_width: {
        if(action == GET) {
          dest[0] = mp_obj_new_int(self->image->bounds().w);
          return;
        }
      };

      case MP_QSTR_height: {
        if(action == GET) {
          dest[0] = mp_obj_new_int(self->image->bounds().h);
          return;
        }
      };

      case MP_QSTR_has_palette: {
        if(action == GET) {
          dest[0] = mp_obj_new_bool(self->image->has_palette());
          return;
        }
      };

      case MP_QSTR_antialias: {
        if(action == GET) {
          dest[0] = mp_obj_new_int(self->image->antialias());
          return;
        }

        if(action == SET) {
          self->image->antialias((antialias_t)mp_obj_get_int(dest[1]));
          dest[0] = MP_OBJ_NULL;
          return;
        }
      };

      case MP_QSTR_alpha: {
        if(action == GET) {
          dest[0] = mp_obj_new_int(self->image->alpha());
          return;
        }

        if(action == SET) {
          self->image->alpha((int)mp_obj_get_int(dest[1]));
          dest[0] = MP_OBJ_NULL;
          return;
        }
      };

      case MP_QSTR_pen: {
        if(action == GET) {
          if(self->brush) {
            dest[0] = self->brush;
          }else{
            dest[0] = mp_const_none;
          }
          return;
        }

        if(action == SET) {
          brush_obj_t *brush = mp_obj_to_brush(1, &dest[1]);
          if(!brush){
            mp_raise_TypeError(MP_ERROR_TEXT("value must be of type brush or color"));
          }
          self->brush = brush;
          self->image->brush(brush->brush);

          dest[0] = MP_OBJ_NULL;
          return;
        }
      };

      case MP_QSTR_font: {
        if(action == GET) {
          if(self->font || self->pixel_font) {
            if(self->font) {
              dest[0] = MP_OBJ_FROM_PTR(self->font);
            }else{
              dest[0] = MP_OBJ_FROM_PTR(self->pixel_font);
            }
          }else{
            dest[0] = mp_const_none;
          }
          return;
        }

        if(action == SET) {
          if(!mp_obj_is_type(dest[1], &type_font) && !mp_obj_is_type(dest[1], &type_pixel_font)) {
            mp_raise_TypeError(MP_ERROR_TEXT("value must be of type Font or PixelFont"));
          }
          if(mp_obj_is_type(dest[1], &type_font)) {
            self->font = (font_obj_t *)dest[1];
            self->pixel_font = nullptr;
            self->image->font(&self->font->font);
          }
          if(mp_obj_is_type(dest[1], &type_pixel_font)) {
            self->pixel_font = (pixel_font_obj_t *)dest[1];
            self->font = nullptr;
            self->image->pixel_font(self->pixel_font->font);
          }
          dest[0] = MP_OBJ_NULL;
          return;
        }
      };
    }

    // we didn't handle this, fall back to alternative methods
    dest[1] = MP_OBJ_SENTINEL;
  })

  static void image_print(const mp_print_t *print, mp_obj_t self_in, mp_print_kind_t kind) {
    self(self_in, image_obj_t);
    mp_printf(print, "image(%d x %d)", int(self->image->bounds().w), int(self->image->bounds().h));
  }

  static mp_int_t image_get_framebuffer(mp_obj_t self_in, mp_buffer_info_t *bufinfo, mp_uint_t flags) {
    self(self_in, image_obj_t);
    bufinfo->buf = self->image->ptr(0, 0);
    bufinfo->len = self->image->buffer_size();
    bufinfo->typecode = 'B';
    return 0;
  }

  /*
    takes a list of commands to perform, each command is a tuple containing the
    method/attribute name and a single argument or tuple of arguments.

    [
      ("clear"),                          # calling a method with no parameters
      ("pen", color.blue),                # setting an attribute
      ("rectangle", (10, 10, 50, 50)),    # calling a raster draw method
      ("circle", (50, 50, 20)),           # calling another raster draw method
      "dither"                            # also calling a method with no parameters
    ]
  */
  MPY_BIND_VAR(2, batch, {
    const image_obj_t *self = (image_obj_t *)MP_OBJ_TO_PTR(args[0]);
    if (!mp_obj_is_type(args[1], &mp_type_list)) {
      mp_raise_TypeError(MP_ERROR_TEXT("invalid parameters, expected list of draw commands"));
    }

    // dummy args object we use to call method handlers
    mp_obj_t handler_args[32];
    handler_args[0] = args[0]; // set "self" ahead of time

    // get the list of commands
    size_t ncommands;
    mp_obj_t *commands;
    mp_obj_list_get(args[1], &ncommands, &commands);

    for(size_t i = 0; i < ncommands; i++) {
      // command can either be a tuple with a qstr and parameters, or just a
      // qstr if the method takes no parameters
      if(!mp_obj_is_type(commands[i], &mp_type_tuple)) {
        mp_raise_TypeError(MP_ERROR_TEXT("list entries must be tuples in the format (command, parameter1, parameter2, ...)"));
      }

      // get the list of commands
      size_t ncommand;
      mp_obj_t *command;
      mp_obj_tuple_get(commands[i], &ncommand, &command);

      qstr name = mp_obj_str_get_qstr(command[0]);

      size_t nparameters = ncommand - 1;
      for(size_t j = 1; j < ncommand; j++) {
        handler_args[j] = command[j];
      }

      if(nparameters == 1) {
        // if a single value provided, attempt to use that to set an
        // attribute
        mp_obj_t dest[2];
        dest[0] = MP_OBJ_SENTINEL;
        dest[1] = handler_args[1];
        image_attr(handler_args[0], name, dest);
        if(dest[0] == MP_OBJ_NULL) {
          // attribute was found and set, skip to next command
          continue;
        }
      }

      // handler is also passed reference to "self"
      size_t nhandler_args = nparameters + 1;
      switch (name) {
        case MP_QSTR_clear: {
          mpy_binding_clear(nhandler_args, handler_args);
        } break;
        case MP_QSTR_rectangle: {
          mpy_binding_rectangle(nhandler_args, handler_args);
        } break;
        case MP_QSTR_line: {
          mpy_binding_line(nhandler_args, handler_args);
        } break;
        case MP_QSTR_circle: {
          mpy_binding_circle(nhandler_args, handler_args);
        } break;
        case MP_QSTR_triangle: {
          mpy_binding_triangle(nhandler_args, handler_args);
        } break;
        case MP_QSTR_put: {
          mpy_binding_put(nhandler_args, handler_args);
        } break;
        case MP_QSTR_blur: {
          mpy_binding_blur(nhandler_args, handler_args);
        } break;
        case MP_QSTR_dither: {
          mpy_binding_dither(nhandler_args, handler_args);
        } break;
        case MP_QSTR_shape: {
          mpy_binding_shape(nhandler_args, handler_args);
        } break;
        case MP_QSTR_text: {
          mpy_binding_text(nhandler_args, handler_args);
        } break;
        case MP_QSTR_blit_vspan: {
          mpy_binding_blit_vspan(nhandler_args, handler_args);
        } break;
        case MP_QSTR_blit_hspan: {
          mpy_binding_blit_hspan(nhandler_args, handler_args);
        } break;
        case MP_QSTR_blit: {
          mpy_binding_blit(nhandler_args, handler_args);
        } break;

        default: mp_raise_ValueError(MP_ERROR_TEXT("unknown method"));
      }
    }

    return mp_const_none;
  })

MPY_BIND_LOCALS_DICT(image,
      { MP_ROM_QSTR(MP_QSTR___del__), MP_ROM_PTR(&image__del___obj) },

      MPY_BIND_ROM_PTR_STATIC(load),
      MPY_BIND_ROM_PTR(load_into),
      MPY_BIND_ROM_PTR(window),

      // primitives
      MPY_BIND_ROM_PTR(clear),
      MPY_BIND_ROM_PTR(rectangle),
      MPY_BIND_ROM_PTR(line),
      MPY_BIND_ROM_PTR(circle),
      MPY_BIND_ROM_PTR(triangle),
      MPY_BIND_ROM_PTR(get),
      MPY_BIND_ROM_PTR(put),

      MPY_BIND_ROM_PTR(blur),
      MPY_BIND_ROM_PTR(dither),
      MPY_BIND_ROM_PTR(onebit),
      MPY_BIND_ROM_PTR(monochrome),

      // vector
      MPY_BIND_ROM_PTR(shape),

      // text
      MPY_BIND_ROM_PTR(text),
      MPY_BIND_ROM_PTR(measure_text),

      // blitting
      MPY_BIND_ROM_PTR(blit_vspan),
      MPY_BIND_ROM_PTR(blit_hspan),
      MPY_BIND_ROM_PTR(blit),

      MPY_BIND_ROM_PTR(batch),

      // TODO: Just define these in MicroPython?
      { MP_ROM_QSTR(MP_QSTR_X4), MP_ROM_INT(antialias_t::X4)},
      { MP_ROM_QSTR(MP_QSTR_X2), MP_ROM_INT(antialias_t::X2)},
      { MP_ROM_QSTR(MP_QSTR_OFF), MP_ROM_INT(antialias_t::OFF)},
)

  MP_DEFINE_CONST_OBJ_TYPE(
      type_image,
      MP_QSTR_image,
      MP_TYPE_FLAG_NONE,
      make_new, (const void *)image_new,
      print, (const void *)image_print,
      attr, (const void *)image_attr,
      buffer, (const void *)image_get_framebuffer,
      locals_dict, &image_locals_dict
  );

}
