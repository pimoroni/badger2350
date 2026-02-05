#ifdef PICO
#include "pico/stdlib.h"
#endif

#include "mp_helpers.hpp"
#include "picovector.hpp"

#define BUTTON_HOME 0b100000
#define BUTTON_A    0b010000
#define BUTTON_B    0b001000
#define BUTTON_C    0b000100
#define BUTTON_UP   0b000010
#define BUTTON_DOWN 0b000001

extern "C" {
  #include "py/runtime.h"
  #include "py/mphal.h"

mp_obj_t ticks;

#ifdef PICO
  uint8_t picovector_buttons;
  uint8_t picovector_changed_buttons;
  mp_uint_t picovector_ticks;
  mp_uint_t picovector_last_ticks;

  extern uint32_t powman_get_user_switches(void);
#else
  extern uint8_t picovector_buttons;
  extern uint8_t picovector_changed_buttons;
  extern double picovector_ticks;
  extern double picovector_last_ticks;
#endif

  MPY_BIND_ATTR(input, {
    (void)self_in;

    if(attr == MP_QSTR_ticks && dest[0] == MP_OBJ_NULL) {
      dest[0] = mp_obj_new_int_from_ll(picovector_ticks);
      return;
    }

    if(attr == MP_QSTR_ticks_delta && dest[0] == MP_OBJ_NULL) {
      dest[0] = mp_obj_new_int_from_ll(picovector_ticks - picovector_last_ticks);
      return;
    }

    if((attr == MP_QSTR_held || attr == MP_QSTR_pressed || attr == MP_QSTR_released || attr == MP_QSTR_changed) && dest[0] == MP_OBJ_NULL) {
      mp_obj_t t_items[6];
      uint8_t buttons = 0;

      switch(attr) {
        case MP_QSTR_held:
          buttons = picovector_buttons;
          break;
        case MP_QSTR_pressed:
          buttons = picovector_buttons & picovector_changed_buttons;
          break;
        case MP_QSTR_released:
          buttons = ~picovector_buttons & picovector_changed_buttons;
          break;
        case MP_QSTR_changed:
          buttons = picovector_changed_buttons;
          break;
        default:
          break;
      }
      int n = 0;
      if(buttons & BUTTON_HOME) {
        t_items[n] = MP_ROM_INT(BUTTON_HOME);
        n++;
      }
      if(buttons & BUTTON_A) {
        t_items[n] = MP_ROM_INT(BUTTON_A);
        n++;
      }
      if(buttons & BUTTON_B) {
        t_items[n] = MP_ROM_INT(BUTTON_B);
        n++;
      }
      if(buttons & BUTTON_C) {
        t_items[n] = MP_ROM_INT(BUTTON_C);
        n++;
      }
      if(buttons & BUTTON_UP) {
        t_items[n] = MP_ROM_INT(BUTTON_UP);
        n++;
      }
      if(buttons & BUTTON_DOWN) {
        t_items[n] = MP_ROM_INT(BUTTON_DOWN);
        n++;
      }
      dest[0] = mp_obj_new_tuple(n, t_items);
      return;
    }

    dest[1] = MP_OBJ_SENTINEL;
  })

  // Call io.poll() to set up frame stable input and tick values
  MPY_BIND_ARGS0(poll, {
#ifdef PICO
    uint8_t buttons = 0;

    // Feed the switch states from wakeup into `pressed`
    static bool got_wakeup_switches = false;
    if(!got_wakeup_switches) {
      uint32_t user_sw = powman_get_user_switches();
      if(user_sw & (1 << BW_SWITCH_A))    buttons |= BUTTON_A;
      if(user_sw & (1 << BW_SWITCH_B))    buttons |= BUTTON_B;
      if(user_sw & (1 << BW_SWITCH_C))    buttons |= BUTTON_C;
      if(user_sw & (1 << BW_SWITCH_UP))   buttons |= BUTTON_UP;
      if(user_sw & (1 << BW_SWITCH_DOWN)) buttons |= BUTTON_DOWN;
      got_wakeup_switches = true;
    }

    buttons |= gpio_get(BW_SWITCH_A)    ? 0 : BUTTON_A;
    buttons |= gpio_get(BW_SWITCH_B)    ? 0 : BUTTON_B;
    buttons |= gpio_get(BW_SWITCH_C)    ? 0 : BUTTON_C;
    buttons |= gpio_get(BW_SWITCH_UP)   ? 0 : BUTTON_UP;
    buttons |= gpio_get(BW_SWITCH_DOWN) ? 0 : BUTTON_DOWN;
    buttons |= gpio_get(BW_SWITCH_HOME) ? 0 : BUTTON_HOME;

    picovector_changed_buttons = buttons ^ picovector_buttons;
    picovector_buttons = buttons;
    picovector_last_ticks = picovector_ticks;
    picovector_ticks = mp_hal_ticks_ms();
#endif
    ticks = mp_obj_new_int_from_ll(picovector_ticks);
    return mp_const_none;
  })

  static const mp_rom_map_elem_t input_globals_table[] = {
    MPY_BIND_ROM_PTR(poll),
    // TODO Move these to MicroPython?
    { MP_ROM_QSTR(MP_QSTR_BUTTON_HOME), MP_ROM_INT(BUTTON_HOME) },
    { MP_ROM_QSTR(MP_QSTR_BUTTON_A),    MP_ROM_INT(BUTTON_A) },
    { MP_ROM_QSTR(MP_QSTR_BUTTON_B),    MP_ROM_INT(BUTTON_B) },
    { MP_ROM_QSTR(MP_QSTR_BUTTON_C),    MP_ROM_INT(BUTTON_C) },
    { MP_ROM_QSTR(MP_QSTR_BUTTON_UP),   MP_ROM_INT(BUTTON_UP) },
    { MP_ROM_QSTR(MP_QSTR_BUTTON_DOWN), MP_ROM_INT(BUTTON_DOWN) },
  };
  static MP_DEFINE_CONST_DICT(input_globals, input_globals_table);

  const mp_obj_module_t mod_input = {
      .base = { &mp_type_module },
      .globals = (mp_obj_dict_t *)&input_globals,
  };

  MP_REGISTER_MODULE(MP_QSTR__input, mod_input);
  MP_REGISTER_MODULE_DELEGATION(mod_input, input_attr);
}

