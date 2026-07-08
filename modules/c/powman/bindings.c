#include <time.h>
#include <sys/time.h>

#include "pico/stdlib.h"
#include "pico/util/datetime.h"
#include "powman.h"

#include "mphalport.h"
#include "py/runtime.h"
#include "shared/timeutils/timeutils.h"

#define GPIO_I2C_POWER 2
#define GPIO_WAKE 3
#define GPIO_EXT_CLK 12
#define GPIO_LED_A 10

enum {
    WAKE_BUTTON_A = 0x00,
    WAKE_BUTTON_B,
    WAKE_BUTTON_C,
    WAKE_BUTTON_UP,
    WAKE_BUTTON_DOWN,
    WAKE_DOUBLETAP,     // Reset was double-pressed
    WAKE_USER_SW,       // User-switch on reverse of board
    WAKE_VBUS_DETECT,   // USB VBUS
    WAKE_RTC,           // Onboard RTC alarm interrupt
    WAKE_ALARM = 0xf0,  // Internal timer timeout
    WAKE_RESET = 0xf1,  // Chip reset low
    WAKE_WATCHDOG = 0xf2, // Watchdog reboot
    WAKE_UNKNOWN = 0xff,
};

void mp_pico_panic(const char *fmt, ...) {
    va_list args;

    if (fmt) {
        va_start(args, fmt);
        int ret = mp_vprintf(&mp_plat_print, fmt, args);
        (void)ret;
        va_end(args);
    }

    while (1) {
        mp_event_handle_nowait();
        sleep_ms(1);
    }
}

mp_obj_t _sleep_get_wake_reason(void) {
    uint8_t wake_reason = powman_get_wake_reason();
    // A software-triggered double-tap (reset_into_msc) reboots via the watchdog,
    // so it looks like a watchdog reset too. Check the double-tap flag first so
    // it wins and main.py enters USB Mass Storage mode rather than plain-booting.
    if(wake_reason & POWMAN_DOUBLETAP)   return MP_ROM_INT(WAKE_DOUBLETAP);
    if(powman_wake_watchdog())           return MP_ROM_INT(WAKE_WATCHDOG);
    if(powman_wake_reset())              return MP_ROM_INT(WAKE_RESET);
    if(wake_reason & POWMAN_WAKE_PWRUP0) return MP_ROM_INT(WAKE_VBUS_DETECT);
    if(wake_reason & POWMAN_WAKE_PWRUP1) return MP_ROM_INT(WAKE_RTC);
    if(wake_reason & POWMAN_WAKE_PWRUP2) return MP_ROM_INT(WAKE_USER_SW);
    if(wake_reason & POWMAN_WAKE_PWRUP3) {
        uint32_t user_sw = powman_get_user_switches();
        // One of the buttons has been pressed? figure out which...
        // Note this is a first input wins scenario, if the user wants more
        // specific information about *which* buttons were pressed at startup
        // (ie: if there are multiple) they should call get_wake_buttons.
        if(user_sw & (1 << BW_SWITCH_A))    return MP_ROM_INT(WAKE_BUTTON_A);
        if(user_sw & (1 << BW_SWITCH_B))    return MP_ROM_INT(WAKE_BUTTON_B);
        if(user_sw & (1 << BW_SWITCH_C))    return MP_ROM_INT(WAKE_BUTTON_C);
        if(user_sw & (1 << BW_SWITCH_UP))   return MP_ROM_INT(WAKE_BUTTON_UP);
        if(user_sw & (1 << BW_SWITCH_DOWN)) return MP_ROM_INT(WAKE_BUTTON_DOWN);
        return MP_ROM_INT(WAKE_UNKNOWN);
    };
    if(wake_reason & POWMAN_WAKE_ALARM)  return MP_ROM_INT(WAKE_ALARM);
    return MP_ROM_INT(WAKE_UNKNOWN);
}
static MP_DEFINE_CONST_FUN_OBJ_0(_sleep_get_wake_reason_obj, _sleep_get_wake_reason);

mp_obj_t _sleep_get_wake_buttons(void) {
    uint32_t user_sw = powman_get_user_switches();
    mp_obj_t tuple_items[5];
    int i = 0;
    if(user_sw & (1 << BW_SWITCH_A)) {tuple_items[i] = machine_pin_find(mp_obj_new_int(BW_SWITCH_A));i++;}
    if(user_sw & (1 << BW_SWITCH_B)) {tuple_items[i] = machine_pin_find(mp_obj_new_int(BW_SWITCH_B));i++;}
    if(user_sw & (1 << BW_SWITCH_C)) {tuple_items[i] = machine_pin_find(mp_obj_new_int(BW_SWITCH_C));i++;}
    if(user_sw & (1 << BW_SWITCH_UP)) {tuple_items[i] = machine_pin_find(mp_obj_new_int(BW_SWITCH_UP));i++;}
    if(user_sw & (1 << BW_SWITCH_DOWN)) {tuple_items[i] = machine_pin_find(mp_obj_new_int(BW_SWITCH_DOWN));i++;}
    return mp_obj_new_tuple(i, tuple_items);
}
static MP_DEFINE_CONST_FUN_OBJ_0(_sleep_get_wake_buttons_obj, _sleep_get_wake_buttons);

/*! \brief Send system to sleep (pressing reset will always wake it)
 */
mp_obj_t _shipping_mode(void) {
    int err;
    powman_init();
    err = powman_off();
    hard_assert(err == PICO_OK);
    hard_assert(false); // should never get here!
    return mp_const_none;
}
static MP_DEFINE_CONST_FUN_OBJ_0(_shipping_mode_obj, _shipping_mode);


/*! \brief Send system to sleep until a button/system interrupt occurs
 *
 * \param timeout wakeup after timeout milliseconds if no edge occurs
 */
mp_obj_t _sleep_sleep(size_t n_args, const mp_obj_t *args) {
    enum { ARG_timeout };

    uint64_t timeout_ms = 0;
    int err;

    if (n_args == 1) {
        timeout_ms = (uint64_t)mp_obj_get_float(args[ARG_timeout]) * 1000;
    }

    powman_init();

    // We must set the pulls on the user buttons or they will not be sufficient
    // to trigger the interrupt pin
    gpio_init_mask(BW_SWITCH_MASK);
    gpio_set_dir_in_masked(BW_SWITCH_MASK);
    gpio_set_pulls(BW_SWITCH_A, true, false);
    gpio_set_pulls(BW_SWITCH_B, true, false);
    gpio_set_pulls(BW_SWITCH_C, true, false);
    gpio_set_pulls(BW_SWITCH_UP, true, false);
    gpio_set_pulls(BW_SWITCH_DOWN, true, false);

    //err = powman_setup_gpio_wakeup(POWMAN_WAKE_PWRUP0_CH, BW_VBUS_DETECT, true, true, 1000);
    err = powman_setup_gpio_wakeup(POWMAN_WAKE_PWRUP1_CH, BW_RTC_ALARM, true, false, 1000);
    //err = powman_setup_gpio_wakeup(POWMAN_WAKE_PWRUP2_CH, BW_RESET_SW, true, true, 1000);
    err = powman_setup_gpio_wakeup(POWMAN_WAKE_PWRUP3_CH, BW_SWITCH_INT, true, false, 1000);


    // power off
    if (timeout_ms > 0) {
        absolute_time_t timeout = make_timeout_time_ms(timeout_ms);
        err = powman_off_until_time(timeout);
    } else {
        err = powman_off();
    }
    hard_assert(err == PICO_OK);
    hard_assert(false); // should never get here!

    return mp_const_none;
}
static MP_DEFINE_CONST_FUN_OBJ_VAR_BETWEEN(_sleep_sleep_obj, 0, 1, _sleep_sleep);

/*! \brief Send system to dormant until the specified time, note for RP2040 the RTC must be driven by an external clock
 *
 * \param ts The time to wake up
 * \param callback Function to call on wakeup.
 */
mp_obj_t _sleep_goto_dormant_until(mp_obj_t absolute_time_in) {
    // Borrowed from https://github.com/micropython/micropython/blob/master/ports/rp2/machine_rtc.c#L83C1-L96
    mp_obj_t *items;
    mp_obj_get_array_fixed_n(absolute_time_in, 8, &items);
    timeutils_struct_time_t tm = {
        .tm_year = mp_obj_get_int(items[0]),
        .tm_mon = mp_obj_get_int(items[1]),
        .tm_mday = mp_obj_get_int(items[2]),
        .tm_hour = mp_obj_get_int(items[4]),
        .tm_min = mp_obj_get_int(items[5]),
        .tm_sec = mp_obj_get_int(items[6]),
    };
    struct timespec ts = { 0, 0 };
    ts.tv_sec = timeutils_seconds_since_epoch(tm.tm_year, tm.tm_mon, tm.tm_mday, tm.tm_hour, tm.tm_min, tm.tm_sec);

    int rc = powman_off_until_time(timespec_to_ms(&ts));
    hard_assert(rc == PICO_OK);
    hard_assert(false); // should never get here!

    return mp_const_none;
}
static MP_DEFINE_CONST_FUN_OBJ_1(_sleep_goto_dormant_until_obj, _sleep_goto_dormant_until);

/*! \brief Send system to dormant until the specified time, note for RP2040 the RTC must be driven by an external clock
 *
 * \param ts The time to wake up
 * \param callback Function to call on wakeup.
 */
mp_obj_t _sleep_goto_dormant_for(mp_obj_t time_seconds_in) {
    uint64_t ms = (uint64_t)(mp_obj_get_float(time_seconds_in) * 1000);
    int rc = powman_off_for_ms(ms);
    hard_assert(rc == PICO_OK);
    hard_assert(false); // should never get here!
    return mp_const_none;
}
static MP_DEFINE_CONST_FUN_OBJ_1(_sleep_goto_dormant_for_obj, _sleep_goto_dormant_for);

static mp_obj_t _test_psram_cs() {
    return mp_obj_new_bool(psram_cs1_pullup_check());
}
static MP_DEFINE_CONST_FUN_OBJ_0(_test_psram_cs_obj, _test_psram_cs);

/*! \brief Reboot cleanly into USB Mass Storage mode
 *
 * Sets the double-tap flag and triggers a watchdog reset. On the next boot the
 * badge reports a WAKE_DOUBLETAP wake reason, so main.py enters MSC mode exactly
 * as if RESET had been physically double-tapped. Does not return.
 */
mp_obj_t _reset_into_msc(void) {
    powman_reset_into_msc();
    return mp_const_none; // should never get here!
}
static MP_DEFINE_CONST_FUN_OBJ_0(_reset_into_msc_obj, _reset_into_msc);

static const mp_map_elem_t sleep_globals_table[] = {
    { MP_ROM_QSTR(MP_QSTR___name__), MP_ROM_QSTR(MP_QSTR_powman) },
    { MP_ROM_QSTR(MP_QSTR_sleep), MP_ROM_PTR(&_sleep_sleep_obj) },
    { MP_ROM_QSTR(MP_QSTR_goto_dormant_until), MP_ROM_PTR(&_sleep_goto_dormant_until_obj) },
    { MP_ROM_QSTR(MP_QSTR_goto_dormant_for), MP_ROM_PTR(&_sleep_goto_dormant_for_obj) },
    { MP_ROM_QSTR(MP_QSTR_get_wake_reason), MP_ROM_PTR(&_sleep_get_wake_reason_obj) },
    { MP_ROM_QSTR(MP_QSTR_get_wake_buttons), MP_ROM_PTR(&_sleep_get_wake_buttons_obj) },
    { MP_ROM_QSTR(MP_QSTR_shipping_mode), MP_ROM_PTR(&_shipping_mode_obj) },
    { MP_ROM_QSTR(MP_QSTR_reset_into_msc), MP_ROM_PTR(&_reset_into_msc_obj) },
    { MP_ROM_QSTR(MP_QSTR__test_psram_cs), MP_ROM_PTR(&_test_psram_cs_obj) },

    { MP_ROM_QSTR(MP_QSTR_WAKE_BUTTON_A), MP_ROM_INT(WAKE_BUTTON_A) },
    { MP_ROM_QSTR(MP_QSTR_WAKE_BUTTON_B), MP_ROM_INT(WAKE_BUTTON_B) },
    { MP_ROM_QSTR(MP_QSTR_WAKE_BUTTON_C), MP_ROM_INT(WAKE_BUTTON_C) },
    { MP_ROM_QSTR(MP_QSTR_WAKE_BUTTON_UP), MP_ROM_INT(WAKE_BUTTON_UP) },
    { MP_ROM_QSTR(MP_QSTR_WAKE_BUTTON_DOWN), MP_ROM_INT(WAKE_BUTTON_DOWN) },
    { MP_ROM_QSTR(MP_QSTR_WAKE_DOUBLETAP), MP_ROM_INT(WAKE_DOUBLETAP) },
    { MP_ROM_QSTR(MP_QSTR_WAKE_USER_SW),  MP_ROM_INT(WAKE_USER_SW)  },
    { MP_ROM_QSTR(MP_QSTR_WAKE_VBUS_DETECT),  MP_ROM_INT(WAKE_VBUS_DETECT)  },
    { MP_ROM_QSTR(MP_QSTR_WAKE_RTC),      MP_ROM_INT(WAKE_RTC)      },
    { MP_ROM_QSTR(MP_QSTR_WAKE_ALARM),    MP_ROM_INT(WAKE_ALARM)    },
    { MP_ROM_QSTR(MP_QSTR_WAKE_RESET),    MP_ROM_INT(WAKE_RESET)    },
    { MP_ROM_QSTR(MP_QSTR_WAKE_WATCHDOG), MP_ROM_INT(WAKE_WATCHDOG) },
    { MP_ROM_QSTR(MP_QSTR_WAKE_UNKNOWN),  MP_ROM_INT(WAKE_UNKNOWN)  },
};
static MP_DEFINE_CONST_DICT(mp_module_sleep_globals, sleep_globals_table);

const mp_obj_module_t sleep_user_cmodule = {
    .base = { &mp_type_module },
    .globals = (mp_obj_dict_t*)&mp_module_sleep_globals,
};

MP_REGISTER_MODULE(MP_QSTR_powman, sleep_user_cmodule);