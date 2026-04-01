#pragma once

extern "C" {
  #include "py/runtime.h"
  #include "py/stream.h"
}

// Binding shortcuts

#define MPY_BIND_STATICMETHOD_ARGS0(fn_name, fn_body) static mp_obj_t mpy_binding_##fn_name(void) fn_body\
  static MP_DEFINE_CONST_FUN_OBJ_0(mpy_binding_##fn_name##_obj, mpy_binding_##fn_name);\
  static MP_DEFINE_CONST_STATICMETHOD_OBJ(mpy_binding_##fn_name##_static_obj, MP_ROM_PTR(&mpy_binding_##fn_name##_obj));

#define MPY_BIND_STATICMETHOD_ARGS1(fn_name, arg1, fn_body) static mp_obj_t mpy_binding_##fn_name(mp_obj_t arg1) fn_body\
  static MP_DEFINE_CONST_FUN_OBJ_1(mpy_binding_##fn_name##_obj, mpy_binding_##fn_name);\
  static MP_DEFINE_CONST_STATICMETHOD_OBJ(mpy_binding_##fn_name##_static_obj, MP_ROM_PTR(&mpy_binding_##fn_name##_obj));

// Var args with lower bounds, static class method
#define MPY_BIND_STATICMETHOD_VAR(var_min_args, fn_name, fn_body) static mp_obj_t mpy_binding_##fn_name(size_t n_args, const mp_obj_t *args) fn_body\
  static MP_DEFINE_CONST_FUN_OBJ_VAR(mpy_binding_##fn_name##_obj, var_min_args, mpy_binding_##fn_name);\
  static MP_DEFINE_CONST_STATICMETHOD_OBJ(mpy_binding_##fn_name##_static_obj, MP_ROM_PTR(&mpy_binding_##fn_name##_obj));

#define MPY_BIND_STATICMETHOD_KW(var_min_args, fn_name, fn_body) static mp_obj_t mpy_binding_##fn_name(size_t n_args, const mp_obj_t *args, mp_map_t *kw_args) fn_body\
  static MP_DEFINE_CONST_FUN_OBJ_KW(mpy_binding_##fn_name##_obj, var_min_args, mpy_binding_##fn_name);\
  static MP_DEFINE_CONST_STATICMETHOD_OBJ(mpy_binding_##fn_name##_static_obj, MP_ROM_PTR(&mpy_binding_##fn_name##_obj));


// Class methods. These have an explicit "self_in".
#define MPY_BIND_CLASSMETHOD_ARGS1(fn_name, arg1, fn_body) static mp_obj_t mpy_binding_##fn_name(mp_obj_t self_in, mp_obj_t arg1) fn_body\
  static MP_DEFINE_CONST_FUN_OBJ_2(mpy_binding_##fn_name##_obj, mpy_binding_##fn_name);

#define MPY_BIND_CLASSMETHOD_ARGS0(fn_name, fn_body) static mp_obj_t mpy_binding_##fn_name(mp_obj_t self_in) fn_body\
  static MP_DEFINE_CONST_FUN_OBJ_1(mpy_binding_##fn_name##_obj, mpy_binding_##fn_name);

#define MPY_BIND_ARGS0(fn_name, fn_body) static mp_obj_t mpy_binding_##fn_name(void) fn_body\
  static MP_DEFINE_CONST_FUN_OBJ_0(mpy_binding_##fn_name##_obj, mpy_binding_##fn_name);

#define MPY_BIND_ARGS1(fn_name, arg1, fn_body) static mp_obj_t mpy_binding_##fn_name(mp_obj_t arg1) fn_body\
  static MP_DEFINE_CONST_FUN_OBJ_1(mpy_binding_##fn_name##_obj, mpy_binding_##fn_name);


// Var args with lower bounds
// Class versions of this method just use args[0] for self, so it needs no special case
#define MPY_BIND_VAR(var_min_args, fn_name, fn_body) static mp_obj_t mpy_binding_##fn_name(size_t n_args, const mp_obj_t *args) fn_body\
  static MP_DEFINE_CONST_FUN_OBJ_VAR(mpy_binding_##fn_name##_obj, var_min_args, mpy_binding_##fn_name);

// "new" / class constructor
#define MPY_BIND_NEW(fn_name, fn_body) static mp_obj_t fn_name##_new(const mp_obj_type_t *type, size_t n_args, size_t n_kw, const mp_obj_t *args) fn_body

#define MPY_BIND_DEL(fn_name, fn_body) static mp_obj_t fn_name##__del__(mp_obj_t self_in) fn_body\
  static MP_DEFINE_CONST_FUN_OBJ_1(fn_name##__del___obj, fn_name##__del__);

// "attr" used for both class attrs and REGISTER_MODULE_DELEGATION
// In the latter case it must not be "static" since it needs to be visible
// to _mp_builtin_module_delegation_table in objmodule.c.o
#define MPY_BIND_ATTR(fn_name, fn_body) void fn_name##_attr(mp_obj_t self_in, qstr attr, mp_obj_t *dest) fn_body

#define MPY_BIND_ROM_PTR(name) { MP_ROM_QSTR(MP_QSTR_##name), MP_ROM_PTR(&mpy_binding_##name##_obj) }
#define MPY_BIND_ROM_PTR_STATIC(name) { MP_ROM_QSTR(MP_QSTR_##name), MP_ROM_PTR(&mpy_binding_##name##_static_obj) }
#define MPY_BIND_ROM_PTR_DEL(name) { MP_ROM_QSTR(MP_QSTR___del__), MP_ROM_PTR(&name##__del___obj) }
#define MPY_BIND_ROM_INT(name, value) { MP_ROM_QSTR(MP_QSTR_##name), MP_ROM_INT(value) }

#define MPY_BIND_LOCALS_DICT(prefix, ...) \
  static const mp_rom_map_elem_t prefix##_locals_dict_table[] = {\
    __VA_ARGS__\
  };\
  static MP_DEFINE_CONST_DICT(prefix##_locals_dict, prefix##_locals_dict_table);

#define MPY_GET_XY_OR_VEC2(_index, _x, _y)\
  float _x;\
  float _y;\
  if (mp_obj_is_vec2(args[_index])) {\
    const vec2_obj_t *vec2 = (vec2_obj_t *)MP_OBJ_TO_PTR(args[_index]);\
    _x = vec2->v.x;\
    _y = vec2->v.y;\
    n_args -=1;\
    args += 1;\
  } else {\
    _x = mp_obj_get_float(args[_index]);\
    _y = mp_obj_get_float(args[_index + 1]);\
    n_args -= 2;\
    args += 2;\
  }\


#define self(self_in, T) T *self = (T *)MP_OBJ_TO_PTR(self_in)
#define m_new_class(cls, ...) new(m_new(cls, 1)) cls(__VA_ARGS__)
#define m_del_class(cls, ptr) ptr->~cls(); m_del(cls, ptr, 1)

constexpr size_t GET = 0b1 << 31;
constexpr size_t SET = 0b1 << 30;
constexpr size_t DELETE = 0b1 << 29;

// m_attr_action, defined in picovector.cpp
typedef size_t action_t;
extern action_t m_attr_action(mp_obj_t *dest);

// file reading helpers, defined in picovector.cpp
extern uint32_t ru32(mp_obj_t file);
extern uint16_t ru16(mp_obj_t file);
extern uint8_t ru8(mp_obj_t file);
extern int8_t rs8(mp_obj_t file);