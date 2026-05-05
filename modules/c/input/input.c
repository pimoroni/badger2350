#include "py/runtime.h"

extern void input_attr(mp_obj_t self_in, qstr attr, mp_obj_t *dest);
extern mp_obj_t mpy_binding_poll(void);

static MP_DEFINE_CONST_FUN_OBJ_0(mpy_binding_poll_obj, mpy_binding_poll);

static const mp_rom_map_elem_t input_globals_table[] = {
    { MP_ROM_QSTR(MP_QSTR_poll), MP_ROM_PTR(&mpy_binding_poll_obj) }
};
static MP_DEFINE_CONST_DICT(input_globals, input_globals_table);

const mp_obj_module_t mod_input = {
    .base = { &mp_type_module },
    .globals = (mp_obj_dict_t *)&input_globals,
};

MP_REGISTER_MODULE(MP_QSTR__input, mod_input);
MP_REGISTER_MODULE_DELEGATION(mod_input, input_attr);
