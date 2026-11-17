#include <string.h>

#include "py/runtime.h"
#include "py/mphal.h"
#include "shared/tinyusb/mp_usbd.h"
#include "shared/tinyusb/mp_usbd_cdc.h"
#include "genhdr/mpversion.h"

#if MICROPY_HW_USB_CDC_AUX

#define CDCAUX_ITF (1)
#define CDCAUX_WRITE_TIMEOUT_MS (500)
#define CDCAUX_IDENT_REQUEST (0x03)
#define CDCAUX_PROTOCOL_VERSION "1"

#ifndef BADGEWARE_MODEL
#define BADGEWARE_MODEL "unknown"
#endif

#ifndef BADGEWARE_VERSION
#define BADGEWARE_VERSION "unknown"
#endif

static const char cdcaux_ident[] =
    "{\"ident\": \"badgeware-ide\", \"protocol\": " CDCAUX_PROTOCOL_VERSION
    ", \"model\": \"" BADGEWARE_MODEL "\", \"version\": \"" BADGEWARE_VERSION "\", \"board\": \"" MICROPY_HW_BOARD_NAME
    "\", \"firmware\": \"" MICROPY_GIT_TAG "\", \"features\": [\"repl\", \"debug\", \"littlefs\"]}\n";

static bool cdcaux_claimed = false;

void mp_usbd_cdc_aux_rx_cb(uint8_t itf) {
    if (itf != CDCAUX_ITF || cdcaux_claimed) {
        return;
    }
    bool requested = false;
    uint8_t buf[32];
    uint32_t count;
    while ((count = tud_cdc_n_read(itf, buf, sizeof(buf))) > 0) {
        requested |= memchr(buf, CDCAUX_IDENT_REQUEST, count) != NULL;
    }
    if (requested) {
        tud_cdc_n_write(itf, cdcaux_ident, sizeof(cdcaux_ident) - 1);
        tud_cdc_n_write_flush(itf);
    }
}

static mp_obj_t cdcaux_claim(mp_obj_t claim_in) {
    cdcaux_claimed = mp_obj_is_true(claim_in);
    return mp_const_none;
}
static MP_DEFINE_CONST_FUN_OBJ_1(cdcaux_claim_obj, cdcaux_claim);

static mp_obj_t cdcaux_connected(void) {
    return mp_obj_new_bool(tud_cdc_n_connected(CDCAUX_ITF));
}
static MP_DEFINE_CONST_FUN_OBJ_0(cdcaux_connected_obj, cdcaux_connected);

static mp_obj_t cdcaux_any(void) {
    mp_usbd_task();
    return MP_OBJ_NEW_SMALL_INT(tud_cdc_n_available(CDCAUX_ITF));
}
static MP_DEFINE_CONST_FUN_OBJ_0(cdcaux_any_obj, cdcaux_any);

static mp_obj_t cdcaux_read(size_t n_args, const mp_obj_t *args) {
    mp_usbd_task();
    mp_int_t available = tud_cdc_n_available(CDCAUX_ITF);
    mp_int_t count = available;
    if (n_args > 0 && args[0] != mp_const_none) {
        count = MIN(count, mp_obj_get_int(args[0]));
    }
    if (count <= 0) {
        return mp_const_none;
    }
    vstr_t vstr;
    vstr_init_len(&vstr, count);
    vstr.len = tud_cdc_n_read(CDCAUX_ITF, vstr.buf, count);
    return mp_obj_new_bytes_from_vstr(&vstr);
}
static MP_DEFINE_CONST_FUN_OBJ_VAR_BETWEEN(cdcaux_read_obj, 0, 1, cdcaux_read);

static mp_obj_t cdcaux_write(mp_obj_t data_in) {
    mp_buffer_info_t bufinfo;
    mp_get_buffer_raise(data_in, &bufinfo, MP_BUFFER_READ);
    const uint8_t *data = bufinfo.buf;
    size_t written = 0;
    mp_uint_t last_write = mp_hal_ticks_ms();
    while (written < bufinfo.len && tud_cdc_n_connected(CDCAUX_ITF)) {
        uint32_t n = MIN(bufinfo.len - written, tud_cdc_n_write_available(CDCAUX_ITF));
        if (n > 0) {
            n = tud_cdc_n_write(CDCAUX_ITF, data + written, n);
        }
        tud_cdc_n_write_flush(CDCAUX_ITF);
        written += n;
        if (n > 0) {
            last_write = mp_hal_ticks_ms();
        } else if ((mp_uint_t)(mp_hal_ticks_ms() - last_write) >= CDCAUX_WRITE_TIMEOUT_MS) {
            break;
        } else {
            mp_event_wait_ms(1);
        }
        mp_usbd_task();
    }
    return MP_OBJ_NEW_SMALL_INT(written);
}
static MP_DEFINE_CONST_FUN_OBJ_1(cdcaux_write_obj, cdcaux_write);

static const mp_rom_map_elem_t cdcaux_globals_table[] = {
    { MP_ROM_QSTR(MP_QSTR___name__), MP_ROM_QSTR(MP_QSTR_cdcaux) },
    { MP_ROM_QSTR(MP_QSTR_claim), MP_ROM_PTR(&cdcaux_claim_obj) },
    { MP_ROM_QSTR(MP_QSTR_connected), MP_ROM_PTR(&cdcaux_connected_obj) },
    { MP_ROM_QSTR(MP_QSTR_any), MP_ROM_PTR(&cdcaux_any_obj) },
    { MP_ROM_QSTR(MP_QSTR_read), MP_ROM_PTR(&cdcaux_read_obj) },
    { MP_ROM_QSTR(MP_QSTR_write), MP_ROM_PTR(&cdcaux_write_obj) },
};
static MP_DEFINE_CONST_DICT(cdcaux_globals, cdcaux_globals_table);

const mp_obj_module_t mod_cdcaux = {
    .base = { &mp_type_module },
    .globals = (mp_obj_dict_t *)&cdcaux_globals,
};

MP_REGISTER_MODULE(MP_QSTR_cdcaux, mod_cdcaux);

#endif
