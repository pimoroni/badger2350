#include "pico/stdlib.h"

#define BUTTON_HOME 0b100000
#define BUTTON_A    0b010000
#define BUTTON_B    0b001000
#define BUTTON_C    0b000100
#define BUTTON_UP   0b000010
#define BUTTON_DOWN 0b000001

extern "C" {
  #include "py/runtime.h"
  #include "py/mphal.h"

  // For machine_pin_find
  #include "machine_pin.h"

  mp_obj_t ticks;

  uint8_t badgeware_buttons;
  uint8_t badgeware_changed_buttons;
  mp_uint_t badgeware_ticks;
  mp_uint_t badgeware_last_ticks;

  extern uint32_t powman_get_user_switches(void);

  void input_attr(mp_obj_t self_in, qstr attr, mp_obj_t *dest) {
    (void)self_in;

    if(attr == MP_QSTR_ticks && dest[0] == MP_OBJ_NULL) {
      dest[0] = mp_obj_new_int_from_ll(badgeware_ticks);
      return;
    }

    if(attr == MP_QSTR_ticks_delta && dest[0] == MP_OBJ_NULL) {
      dest[0] = mp_obj_new_int_from_ll(badgeware_ticks - badgeware_last_ticks);
      return;
    }

    if((attr == MP_QSTR_held || attr == MP_QSTR_pressed || attr == MP_QSTR_released || attr == MP_QSTR_changed) && dest[0] == MP_OBJ_NULL) {
      mp_obj_t t_items[6];
      uint8_t buttons = 0;

      switch(attr) {
        case MP_QSTR_held:
          buttons = badgeware_buttons;
          break;
        case MP_QSTR_pressed:
          buttons = badgeware_buttons & badgeware_changed_buttons;
          break;
        case MP_QSTR_released:
          buttons = ~badgeware_buttons & badgeware_changed_buttons;
          break;
        case MP_QSTR_changed:
          buttons = badgeware_changed_buttons;
          break;
        default:
          break;
      }
      int n = 0;
      if(buttons & BUTTON_HOME) {
        t_items[n] = MP_OBJ_FROM_PTR(machine_pin_find(MP_ROM_INT(BW_SWITCH_HOME)));
        n++;
      }
      if(buttons & BUTTON_A) {
        t_items[n] = MP_OBJ_FROM_PTR(machine_pin_find(MP_ROM_INT(BW_SWITCH_A)));
        n++;
      }
      if(buttons & BUTTON_B) {
        t_items[n] = MP_OBJ_FROM_PTR(machine_pin_find(MP_ROM_INT(BW_SWITCH_B)));
        n++;
      }
      if(buttons & BUTTON_C) {
        t_items[n] = MP_OBJ_FROM_PTR(machine_pin_find(MP_ROM_INT(BW_SWITCH_C)));
        n++;
      }
      if(buttons & BUTTON_UP) {
        t_items[n] = MP_OBJ_FROM_PTR(machine_pin_find(MP_ROM_INT(BW_SWITCH_UP)));
        n++;
      }
      if(buttons & BUTTON_DOWN) {
        t_items[n] = MP_OBJ_FROM_PTR(machine_pin_find(MP_ROM_INT(BW_SWITCH_DOWN)));
        n++;
      }
      dest[0] = mp_obj_new_tuple(n, t_items);
      return;
    }

    dest[1] = MP_OBJ_SENTINEL;
  }

  // Call io.poll() to set up frame stable input and tick values
  mp_obj_t mpy_binding_poll(void) {
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

    badgeware_changed_buttons = buttons ^ badgeware_buttons;
    badgeware_buttons = buttons;
    badgeware_last_ticks = badgeware_ticks;
    badgeware_ticks = mp_hal_ticks_ms();

    ticks = mp_obj_new_int_from_ll(badgeware_ticks);
    return mp_const_none;
  }
}
