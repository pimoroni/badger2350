
#include "py/runtime.h"
#include "types.h"

// modpicovector
extern mp_obj_t modpicovector___init__(void);
static MP_DEFINE_CONST_FUN_OBJ_0(modpicovector___init___obj, modpicovector___init__);

static const mp_rom_map_elem_t modpicovector_globals_table[] = {
    { MP_ROM_QSTR(MP_QSTR___name__), MP_ROM_QSTR(MP_QSTR_modpicovector) },
    { MP_ROM_QSTR(MP_QSTR___init__), MP_ROM_PTR(&modpicovector___init___obj) },
    { MP_ROM_QSTR(MP_QSTR_brush),  MP_ROM_PTR(&type_brush) },
    { MP_ROM_QSTR(MP_QSTR_color),  MP_ROM_PTR(&type_color) },
    { MP_ROM_QSTR(MP_QSTR_rect),  MP_ROM_PTR(&type_rect) },
    { MP_ROM_QSTR(MP_QSTR_vec2),  MP_ROM_PTR(&type_vec2) },
    { MP_ROM_QSTR(MP_QSTR_shape),  MP_ROM_PTR(&type_shape) },
    { MP_ROM_QSTR(MP_QSTR_image),  MP_ROM_PTR(&type_image) },
    { MP_ROM_QSTR(MP_QSTR_font),  MP_ROM_PTR(&type_font) },
    { MP_ROM_QSTR(MP_QSTR_algorithm),  MP_ROM_PTR(&type_algorithm) },
    { MP_ROM_QSTR(MP_QSTR_pixel_font),  MP_ROM_PTR(&type_pixel_font) },
    { MP_ROM_QSTR(MP_QSTR_mat3),  MP_ROM_PTR(&type_mat3) },
};
static MP_DEFINE_CONST_DICT(modpicovector_globals, modpicovector_globals_table);


// Define module object.
const mp_obj_module_t modpicovector = {
    .base = { &mp_type_module },
    .globals = (mp_obj_dict_t *)&modpicovector_globals,
};

MP_REGISTER_MODULE(MP_QSTR_picovector, modpicovector);