#include <cstdio>
#include "hardware/spi.h"
#include "hardware/sync.h"
#include "pico/binary_info.h"
#include "pico/stdlib.h"
#include <new>  // for placement new

#include "ssd1680.hpp"

using namespace pimoroni;

static SSD1680 *display = nullptr;
static uint32_t display_refcount = 0;

#define MP_OBJ_TO_PTR2(o, t) ((t *)(uintptr_t)(o))
#define m_new_class(cls, ...) new(m_new(cls, 1)) cls(__VA_ARGS__)
#define m_del_class(cls, ptr) ptr->~cls();m_del(cls, ptr, 1)

extern "C" {
#include "ssd1680_bindings.h"
#include "py/builtin.h"

typedef struct _SSD1680_obj_t {
    mp_obj_base_t base;
    SSD1680 *display;
} SSD1680_obj_t;


mp_obj_t ssd1680_make_new(const mp_obj_type_t *type, size_t n_args, size_t n_kw, const mp_obj_t *all_args) {
    _SSD1680_obj_t *self = mp_obj_malloc_with_finaliser(SSD1680_obj_t, &SSD1680_type);
    if(!display) {
        display = m_new_class(SSD1680);
    }
    self->display = display;
    display_refcount++;
    return MP_OBJ_FROM_PTR(self);
}

mp_obj_t ssd1680___del__(mp_obj_t self_in) {
    display_refcount--;
    if(display_refcount == 0) {
        m_del_class(SSD1680, display);
        display = nullptr;
    }
    return mp_const_none;
}

mp_obj_t ssd1680_blocking(mp_obj_t self_in, mp_obj_t blocking_in) {
    (void)self_in;
    display->set_blocking(mp_obj_is_true(blocking_in));
    return mp_const_none;
}

mp_obj_t ssd1680_busy(mp_obj_t self_in) {
    (void)self_in;
    return mp_obj_new_bool(display->is_busy());
}

mp_obj_t ssd1680_update_speed(mp_obj_t self_in, mp_obj_t speed_in) {
    (void)self_in;
    display->set_update_speed(mp_obj_get_int(speed_in));
    return mp_const_none;
}

mp_obj_t ssd1680_update(mp_obj_t self_in) {
    (void)self_in;
    display->update();
    return mp_const_none;
}

mp_obj_t ssd1680_command(mp_obj_t self_in, mp_obj_t reg_in, mp_obj_t data_in) {
    (void)self_in;
    uint8_t reg = mp_obj_get_int(reg_in);

    if(mp_obj_is_type(data_in, &mp_type_tuple)) {
        mp_obj_tuple_t *tuple = (mp_obj_tuple_t *)MP_OBJ_TO_PTR(data_in);
        uint8_t data[tuple->len] = {0};
        for(unsigned i = 0u; i < tuple->len; i++) {
            data[i] = mp_obj_get_int(tuple->items[i]);
        }
        display->command(reg, tuple->len, (const uint8_t *)data);
        return mp_const_none;
    }

    display->command(reg, 0, NULL);
    return mp_const_none;
}

mp_int_t ssd1680_get_framebuffer(mp_obj_t self_in, mp_buffer_info_t *bufinfo, mp_uint_t flags) {
    (void)self_in;
    (void)flags;
    bufinfo->buf = display->get_framebuffer();
    bufinfo->len = 264 * 176 * 4;
    bufinfo->typecode = 'B';
    return 0;
}

}