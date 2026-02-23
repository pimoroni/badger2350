#include "py/runtime.h"
#include "py/objstr.h"

extern const mp_obj_type_t SSD1680_type;

// Declare the functions we'll make available in Python
extern mp_obj_t ssd1680_make_new(const mp_obj_type_t *type, size_t n_args, size_t n_kw, const mp_obj_t *all_args);
extern mp_obj_t ssd1680___del__(mp_obj_t self_in);
extern mp_obj_t ssd1680_update(mp_obj_t self_in);
extern mp_int_t ssd1680_get_framebuffer(mp_obj_t self_in, mp_buffer_info_t *bufinfo, mp_uint_t flags);
extern mp_obj_t ssd1680_command(mp_obj_t self_in, mp_obj_t reg_in, mp_obj_t data_in);
extern mp_obj_t ssd1680_update_speed(mp_obj_t self_in, mp_obj_t speed_in);
extern mp_obj_t ssd1680_blocking(mp_obj_t self_in, mp_obj_t blocking_in);
extern mp_obj_t ssd1680_busy(mp_obj_t self_in);