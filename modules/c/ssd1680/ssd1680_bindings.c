#include "ssd1680_bindings.h"

/***** Module Functions *****/

static MP_DEFINE_CONST_FUN_OBJ_1(ssd1680___del___obj, ssd1680___del__);
static MP_DEFINE_CONST_FUN_OBJ_1(ssd1680_update_obj, ssd1680_update);
static MP_DEFINE_CONST_FUN_OBJ_3(ssd1680_command_obj, ssd1680_command);
static MP_DEFINE_CONST_FUN_OBJ_2(ssd1680_update_speed_obj, ssd1680_update_speed);
static MP_DEFINE_CONST_FUN_OBJ_2(ssd1680_blocking_obj, ssd1680_blocking);
static MP_DEFINE_CONST_FUN_OBJ_1(ssd1680_busy_obj, ssd1680_busy);

/* Class Methods */
static const mp_rom_map_elem_t ssd1680_locals[] = {
    { MP_ROM_QSTR(MP_QSTR___del__), MP_ROM_PTR(&ssd1680___del___obj) },
    { MP_ROM_QSTR(MP_QSTR_update), MP_ROM_PTR(&ssd1680_update_obj) },
    { MP_ROM_QSTR(MP_QSTR_command), MP_ROM_PTR(&ssd1680_command_obj) },
    { MP_ROM_QSTR(MP_QSTR_speed), MP_ROM_PTR(&ssd1680_update_speed_obj) },
    { MP_ROM_QSTR(MP_QSTR_blocking), MP_ROM_PTR(&ssd1680_blocking_obj) },
    { MP_ROM_QSTR(MP_QSTR_busy), MP_ROM_PTR(&ssd1680_busy_obj) },
    { MP_ROM_QSTR(MP_QSTR_WIDTH), MP_ROM_INT(264) },
    { MP_ROM_QSTR(MP_QSTR_HEIGHT), MP_ROM_INT(176) },
};
static MP_DEFINE_CONST_DICT(mp_module_ssd1680_locals, ssd1680_locals);

MP_DEFINE_CONST_OBJ_TYPE(
    SSD1680_type,
    MP_QSTR_SSD1680,
    MP_TYPE_FLAG_NONE,
    make_new, ssd1680_make_new,
    buffer, ssd1680_get_framebuffer,
    locals_dict, (mp_obj_dict_t*)&mp_module_ssd1680_locals
);

/* Module Globals */
static const mp_map_elem_t ssd1680_globals[] = {
    { MP_OBJ_NEW_QSTR(MP_QSTR___name__), MP_OBJ_NEW_QSTR(MP_QSTR_ssd1680) },
    { MP_OBJ_NEW_QSTR(MP_QSTR_SSD1680), (mp_obj_t)&SSD1680_type },
    { MP_ROM_QSTR(MP_QSTR_WIDTH), MP_ROM_INT(264) },
    { MP_ROM_QSTR(MP_QSTR_HEIGHT), MP_ROM_INT(176) },
    { MP_ROM_QSTR(MP_QSTR_TURBO), MP_ROM_INT(3)},
    { MP_ROM_QSTR(MP_QSTR_FAST), MP_ROM_INT(2)},
    { MP_ROM_QSTR(MP_QSTR_NORMAL), MP_ROM_INT(1)},
    { MP_ROM_QSTR(MP_QSTR_SLOW), MP_ROM_INT(0)},
};
static MP_DEFINE_CONST_DICT(mp_module_ssd1680_globals, ssd1680_globals);

const mp_obj_module_t ssd1680_user_cmodule = {
    .base = { &mp_type_module },
    .globals = (mp_obj_dict_t*)&mp_module_ssd1680_globals,
};

MP_REGISTER_MODULE(MP_QSTR_ssd1680, ssd1680_user_cmodule);
