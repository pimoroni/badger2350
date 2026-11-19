#include <string.h>

#include "py/runtime.h"
#include "py/mphal.h"
#include "py/stream.h"
#include "extmod/vfs.h"
#include "shared/tinyusb/mp_usbd.h"
#include "shared/tinyusb/mp_usbd_cdc.h"
#include "genhdr/mpversion.h"
#include "cdcaux.h"

#if MICROPY_HW_USB_CDC_AUX

#define CDCAUX_ITF (1)
#define CDCAUX_WRITE_TIMEOUT_MS (500)
#define CDCAUX_IDENT_REQUEST (0x03)
#define CDCAUX_PROTOCOL_VERSION "1"
#define CDCAUX_LINE_MAX (1024)
#define CDCAUX_INBOX_MAX (4096)
#define CDCAUX_COMMANDS_PER_SERVICE (8)

#ifndef BADGEWARE_MODEL
#define BADGEWARE_MODEL "unknown"
#endif

#ifndef BADGEWARE_VERSION
#define BADGEWARE_VERSION "unknown"
#endif

static const char cdcaux_ident[] =
    "{\"ident\": \"badgeware-ide\", \"protocol\": " CDCAUX_PROTOCOL_VERSION
    ", \"model\": \"" BADGEWARE_MODEL "\", \"version\": \"" BADGEWARE_VERSION "\", \"board\": \"" MICROPY_HW_BOARD_NAME
    "\", \"firmware\": \"" MICROPY_GIT_TAG "\", \"features\": [\"repl\", \"debug\", \"littlefs\", \"fs\", \"app\"]}\n";

typedef struct _cdcaux_buffers_t {
    uint8_t line[CDCAUX_LINE_MAX];
    uint8_t payload[CDCAUX_CHUNK];
    uint8_t inbox[CDCAUX_INBOX_MAX];
} cdcaux_buffers_t;

MP_REGISTER_ROOT_POINTER(struct _cdcaux_buffers_t *cdcaux_buffers);

static const cdcaux_role_t *const cdcaux_roles[] = {
    &cdcaux_app_role,
    &cdcaux_fs_role,
};

static bool cdcaux_claimed = false;
static mp_sched_node_t cdcaux_node;
static volatile uint32_t cdcaux_guard_depth = 0;
static volatile bool cdcaux_service_pending = false;
static bool cdcaux_was_connected = false;

static uint8_t cdcaux_stage[64];
static size_t cdcaux_stage_pos = 0;
static size_t cdcaux_stage_len = 0;

static size_t cdcaux_line_len = 0;
static bool cdcaux_line_overflow = false;
static bool cdcaux_line_ready = false;

static size_t cdcaux_payload_expected = 0;
static size_t cdcaux_payload_received = 0;
static bool cdcaux_payload_discard = false;

static size_t cdcaux_inbox_len = 0;

static void cdcaux_guard_enter(void) {
    cdcaux_guard_depth++;
}

static void cdcaux_guard_exit(void) {
    cdcaux_guard_depth--;
    if (cdcaux_guard_depth == 0 && cdcaux_service_pending) {
        cdcaux_service_pending = false;
        cdcaux_schedule();
    }
}

static void cdcaux_node_callback(mp_sched_node_t *node) {
    (void)node;
    cdcaux_service();
}

void cdcaux_schedule(void) {
    mp_sched_schedule_node(&cdcaux_node, cdcaux_node_callback);
}

void mp_usbd_cdc_aux_rx_cb(uint8_t itf) {
    if (itf == CDCAUX_ITF) {
        cdcaux_schedule();
    }
}

static size_t cdcaux_send(const uint8_t *data, size_t len) {
    size_t written = 0;
    mp_uint_t last_write = mp_hal_ticks_ms();
    while (written < len && tud_cdc_n_connected(CDCAUX_ITF)) {
        uint32_t n = MIN(len - written, tud_cdc_n_write_available(CDCAUX_ITF));
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
    return written;
}

void cdcaux_print_str(const mp_print_t *print, const char *str) {
    mp_obj_print_helper(print, mp_obj_new_str(str, strlen(str)), PRINT_JSON);
}

void cdcaux_reply_begin(cdcaux_reply_t *reply, const char *event, mp_obj_t id) {
    vstr_init_print(&reply->vstr, 128, &reply->print);
    mp_printf(&reply->print, "{\"event\": \"%s\"", event);
    if (id != MP_OBJ_NULL) {
        mp_print_str(&reply->print, ", \"id\": ");
        mp_obj_print_helper(&reply->print, id, PRINT_JSON);
    }
}

void cdcaux_reply_send(cdcaux_reply_t *reply, const uint8_t *payload, size_t payload_len) {
    if (payload != NULL) {
        mp_printf(&reply->print, ", \"bytes\": %u", (unsigned int)payload_len);
    }
    vstr_add_str(&reply->vstr, "}\n");
    cdcaux_send((const uint8_t *)reply->vstr.buf, reply->vstr.len);
    if (payload != NULL && payload_len > 0) {
        cdcaux_send(payload, payload_len);
    }
    vstr_clear(&reply->vstr);
}

void cdcaux_reply_ok(const char *event, mp_obj_t id) {
    cdcaux_reply_t reply;
    cdcaux_reply_begin(&reply, event, id);
    cdcaux_reply_send(&reply, NULL, 0);
}

mp_int_t cdcaux_exception_errno(mp_obj_t exc) {
    if (!mp_obj_is_subclass_fast(MP_OBJ_FROM_PTR(mp_obj_get_type(exc)), MP_OBJ_FROM_PTR(&mp_type_OSError))) {
        return 0;
    }
    mp_obj_t value = mp_obj_exception_get_value(exc);
    return mp_obj_is_small_int(value) ? MP_OBJ_SMALL_INT_VALUE(value) : 0;
}

static const char *cdcaux_errno_name(mp_int_t err) {
    switch (err) {
        case MP_ENOENT:
            return "ENOENT";
        case MP_EIO:
            return "EIO";
        case MP_EBADF:
            return "EBADF";
        case MP_ENOMEM:
            return "ENOMEM";
        case MP_EBUSY:
            return "EBUSY";
        case MP_EEXIST:
            return "EEXIST";
        case MP_ENOTDIR:
            return "ENOTDIR";
        case MP_EISDIR:
            return "EISDIR";
        case MP_EINVAL:
            return "EINVAL";
        case MP_ENOSPC:
            return "ENOSPC";
        case MP_EROFS:
            return "EROFS";
        case MP_EPERM:
            return "EPERM";
        case CDCAUX_ENAMETOOLONG:
            return "ENAMETOOLONG";
        case CDCAUX_ENOTEMPTY:
            return "ENOTEMPTY";
        case CDCAUX_ECORRUPT:
            return "ECORRUPT";
        default:
            return "EIO";
    }
}

static void cdcaux_reply_error(mp_obj_t id, mp_obj_t exc) {
    mp_int_t err = cdcaux_exception_errno(exc);
    if (err == 0 && mp_obj_is_subclass_fast(MP_OBJ_FROM_PTR(mp_obj_get_type(exc)), MP_OBJ_FROM_PTR(&mp_type_MemoryError))) {
        err = MP_ENOMEM;
    }
    vstr_t message;
    mp_print_t message_print;
    vstr_init_print(&message, 64, &message_print);
    mp_printf(&message_print, "%q: ", mp_obj_get_type(exc)->name);
    mp_obj_print_helper(&message_print, exc, PRINT_STR);

    cdcaux_reply_t reply;
    cdcaux_reply_begin(&reply, "error", id);
    mp_printf(&reply.print, ", \"errno\": \"%s\", \"message\": ", cdcaux_errno_name(err));
    mp_obj_print_helper(&reply.print, mp_obj_new_str_from_vstr(&message), PRINT_JSON);
    cdcaux_reply_send(&reply, NULL, 0);
}

mp_obj_t cdcaux_get(mp_obj_t request, qstr key) {
    mp_map_elem_t *elem = mp_map_lookup(mp_obj_dict_get_map(request), MP_OBJ_NEW_QSTR(key), MP_MAP_LOOKUP);
    return elem == NULL ? MP_OBJ_NULL : elem->value;
}

const char *cdcaux_get_str(mp_obj_t request, qstr key) {
    mp_obj_t value = cdcaux_get(request, key);
    if (value == MP_OBJ_NULL || !mp_obj_is_str(value)) {
        mp_raise_OSError(MP_EINVAL);
    }
    return mp_obj_str_get_str(value);
}

mp_int_t cdcaux_get_int(mp_obj_t request, qstr key, mp_int_t default_value) {
    mp_obj_t value = cdcaux_get(request, key);
    if (value == MP_OBJ_NULL || value == mp_const_none) {
        return default_value;
    }
    if (!mp_obj_is_int(value)) {
        mp_raise_OSError(MP_EINVAL);
    }
    return mp_obj_get_int(value);
}

bool cdcaux_get_bool(mp_obj_t request, qstr key) {
    mp_obj_t value = cdcaux_get(request, key);
    return value != MP_OBJ_NULL && mp_obj_is_true(value);
}

static cdcaux_buffers_t *cdcaux_buffers(void) {
    if (MP_STATE_VM(cdcaux_buffers) == NULL) {
        MP_STATE_VM(cdcaux_buffers) = m_new_obj(cdcaux_buffers_t);
    }
    return MP_STATE_VM(cdcaux_buffers);
}

static mp_obj_t cdcaux_parse(const uint8_t *line, size_t len) {
    nlr_buf_t nlr;
    if (nlr_push(&nlr) == 0) {
        mp_obj_t json = mp_import_name(MP_QSTR_json, mp_const_none, MP_OBJ_NEW_SMALL_INT(0));
        mp_obj_t request = mp_call_function_1(mp_load_attr(json, MP_QSTR_loads), mp_obj_new_str((const char *)line, len));
        nlr_pop();
        if (!mp_obj_is_type(request, &mp_type_dict)) {
            return MP_OBJ_NULL;
        }
        return request;
    }
    return MP_OBJ_NULL;
}

static const char *cdcaux_role_cmd(mp_obj_t request) {
    if (request == MP_OBJ_NULL) {
        return NULL;
    }
    mp_obj_t cmd = cdcaux_get(request, MP_QSTR_cmd);
    if (cmd == MP_OBJ_NULL || !mp_obj_is_str(cmd)) {
        return NULL;
    }
    const char *name = mp_obj_str_get_str(cmd);
    for (size_t i = 0; i < MP_ARRAY_SIZE(cdcaux_roles); i++) {
        const char *prefix = cdcaux_roles[i]->prefix;
        if (strncmp(name, prefix, strlen(prefix)) == 0) {
            return name;
        }
    }
    return NULL;
}

static void cdcaux_execute(mp_obj_t request, const char *cmd, const uint8_t *payload, size_t payload_len) {
    mp_obj_t id = cdcaux_get(request, MP_QSTR_id);
    if (id == MP_OBJ_NULL) {
        id = mp_const_none;
    }
    cdcaux_app_touch();
    nlr_buf_t nlr;
    if (nlr_push(&nlr) == 0) {
        bool handled = false;
        for (size_t i = 0; i < MP_ARRAY_SIZE(cdcaux_roles) && !handled; i++) {
            handled = cdcaux_roles[i]->dispatch(cmd, request, id, payload, payload_len);
        }
        if (!handled) {
            mp_raise_OSError(MP_EINVAL);
        }
        nlr_pop();
    } else {
        mp_obj_t exc = MP_OBJ_FROM_PTR(nlr.ret_val);
        if (mp_obj_is_subclass_fast(MP_OBJ_FROM_PTR(mp_obj_get_type(exc)), MP_OBJ_FROM_PTR(&mp_type_KeyboardInterrupt))) {
            mp_sched_keyboard_interrupt();
        }
        cdcaux_reply_error(id, exc);
    }
}

static void cdcaux_line_done(void) {
    cdcaux_line_len = 0;
    cdcaux_line_ready = false;
}

static bool cdcaux_route_line(cdcaux_buffers_t *buffers) {
    if (cdcaux_line_overflow) {
        cdcaux_line_overflow = false;
        cdcaux_line_done();
        cdcaux_reply_error(mp_const_none, mp_obj_new_exception_arg1(&mp_type_OSError, MP_OBJ_NEW_SMALL_INT(MP_EINVAL)));
        return true;
    }

    mp_obj_t request = cdcaux_parse(buffers->line, cdcaux_line_len);
    const char *cmd = cdcaux_role_cmd(request);

    if (cmd == NULL) {
        if (cdcaux_claimed) {
            if (cdcaux_inbox_len + cdcaux_line_len + 1 > CDCAUX_INBOX_MAX) {
                return false;
            }
            memcpy(buffers->inbox + cdcaux_inbox_len, buffers->line, cdcaux_line_len);
            cdcaux_inbox_len += cdcaux_line_len;
            buffers->inbox[cdcaux_inbox_len++] = '\n';
        }
        cdcaux_line_done();
        return true;
    }

    if (!cdcaux_fs_ready() || cdcaux_app_reset_pending()) {
        return false;
    }

    mp_obj_t bytes = cdcaux_get(request, MP_QSTR_bytes);
    mp_int_t expected = (bytes != MP_OBJ_NULL && mp_obj_is_small_int(bytes)) ? MP_OBJ_SMALL_INT_VALUE(bytes) : 0;
    if (expected > 0) {
        cdcaux_payload_expected = expected;
        cdcaux_payload_received = 0;
        cdcaux_payload_discard = expected > CDCAUX_CHUNK;
        cdcaux_line_ready = false;
        return true;
    }

    cdcaux_execute(request, cmd, NULL, 0);
    cdcaux_line_done();
    return true;
}

static void cdcaux_payload_done(cdcaux_buffers_t *buffers) {
    size_t payload_len = cdcaux_payload_received;
    bool discard = cdcaux_payload_discard;
    cdcaux_payload_expected = 0;
    cdcaux_payload_received = 0;
    cdcaux_payload_discard = false;

    mp_obj_t request = cdcaux_parse(buffers->line, cdcaux_line_len);
    const char *cmd = cdcaux_role_cmd(request);
    cdcaux_line_done();
    if (cmd == NULL) {
        return;
    }
    if (discard) {
        mp_obj_t id = cdcaux_get(request, MP_QSTR_id);
        cdcaux_reply_error(id == MP_OBJ_NULL ? mp_const_none : id, mp_obj_new_exception_arg1(&mp_type_OSError, MP_OBJ_NEW_SMALL_INT(MP_EINVAL)));
        return;
    }
    cdcaux_execute(request, cmd, buffers->payload, payload_len);
}

static bool cdcaux_stage_fill(void) {
    if (cdcaux_stage_pos < cdcaux_stage_len) {
        return true;
    }
    cdcaux_stage_pos = 0;
    cdcaux_stage_len = tud_cdc_n_read(CDCAUX_ITF, cdcaux_stage, sizeof(cdcaux_stage));
    return cdcaux_stage_len > 0;
}

static bool cdcaux_read_payload(cdcaux_buffers_t *buffers) {
    size_t wanted = cdcaux_payload_expected - cdcaux_payload_received;
    size_t count;
    if (cdcaux_stage_pos < cdcaux_stage_len) {
        count = MIN(wanted, cdcaux_stage_len - cdcaux_stage_pos);
        if (!cdcaux_payload_discard) {
            memcpy(buffers->payload + cdcaux_payload_received, cdcaux_stage + cdcaux_stage_pos, count);
        }
        cdcaux_stage_pos += count;
    } else if (cdcaux_payload_discard) {
        count = tud_cdc_n_read(CDCAUX_ITF, cdcaux_stage, MIN(wanted, sizeof(cdcaux_stage)));
        cdcaux_stage_pos = 0;
        cdcaux_stage_len = 0;
    } else {
        count = tud_cdc_n_read(CDCAUX_ITF, buffers->payload + cdcaux_payload_received, wanted);
    }
    cdcaux_payload_received += count;
    return count > 0;
}

static void cdcaux_process_rx(cdcaux_buffers_t *buffers) {
    int budget = CDCAUX_COMMANDS_PER_SERVICE;
    while (budget > 0) {
        if (cdcaux_line_ready) {
            if (!cdcaux_route_line(buffers)) {
                return;
            }
            budget--;
            continue;
        }

        if (cdcaux_payload_expected > 0) {
            if (!cdcaux_read_payload(buffers)) {
                return;
            }
            if (cdcaux_payload_received == cdcaux_payload_expected) {
                cdcaux_payload_done(buffers);
                budget--;
            }
            continue;
        }

        if (!cdcaux_stage_fill()) {
            return;
        }
        uint8_t byte = cdcaux_stage[cdcaux_stage_pos++];
        if (byte == CDCAUX_IDENT_REQUEST) {
            cdcaux_send((const uint8_t *)cdcaux_ident, sizeof(cdcaux_ident) - 1);
        } else if (byte == '\n') {
            cdcaux_line_ready = true;
        } else if (byte != '\r') {
            if (cdcaux_line_len < CDCAUX_LINE_MAX) {
                buffers->line[cdcaux_line_len++] = byte;
            } else {
                cdcaux_line_overflow = true;
            }
        }
    }
    cdcaux_schedule();
}

static void cdcaux_rx_reset(void) {
    cdcaux_stage_pos = 0;
    cdcaux_stage_len = 0;
    cdcaux_line_len = 0;
    cdcaux_line_overflow = false;
    cdcaux_line_ready = false;
    cdcaux_payload_expected = 0;
    cdcaux_payload_received = 0;
    cdcaux_payload_discard = false;
    cdcaux_inbox_len = 0;
}

void cdcaux_service(void) {
    if (cdcaux_guard_depth > 0) {
        cdcaux_service_pending = true;
        return;
    }
    cdcaux_guard_enter();
    nlr_buf_t nlr;
    if (nlr_push(&nlr) == 0) {
        cdcaux_buffers_t *buffers = cdcaux_buffers();
        bool connected = tud_cdc_n_connected(CDCAUX_ITF);
        if (cdcaux_was_connected && !connected) {
            cdcaux_rx_reset();
            tud_cdc_n_read_flush(CDCAUX_ITF);
            for (size_t i = 0; i < MP_ARRAY_SIZE(cdcaux_roles); i++) {
                cdcaux_roles[i]->disconnected();
            }
        }
        cdcaux_was_connected = connected;
        for (size_t i = 0; i < MP_ARRAY_SIZE(cdcaux_roles); i++) {
            cdcaux_roles[i]->service(connected);
        }
        cdcaux_process_rx(buffers);
        nlr_pop();
    } else {
        mp_obj_t exc = MP_OBJ_FROM_PTR(nlr.ret_val);
        if (mp_obj_is_subclass_fast(MP_OBJ_FROM_PTR(mp_obj_get_type(exc)), MP_OBJ_FROM_PTR(&mp_type_KeyboardInterrupt))) {
            mp_sched_keyboard_interrupt();
        }
    }
    cdcaux_guard_exit();
}

void cdcaux_soft_reset(void) {
    cdcaux_claimed = false;
    cdcaux_guard_depth = 0;
    cdcaux_service_pending = false;
    MP_STATE_VM(cdcaux_buffers) = NULL;
    cdcaux_rx_reset();
    for (size_t i = 0; i < MP_ARRAY_SIZE(cdcaux_roles); i++) {
        cdcaux_roles[i]->soft_reset();
    }
}

typedef struct _cdcaux_block_device_obj_t {
    mp_obj_base_t base;
    mp_obj_t readblocks[2];
    mp_obj_t writeblocks[2];
    mp_obj_t ioctl[2];
} cdcaux_block_device_obj_t;

static mp_obj_t cdcaux_block_device_make_new(const mp_obj_type_t *type, size_t n_args, size_t n_kw, const mp_obj_t *args) {
    mp_arg_check_num(n_args, n_kw, 1, 1, false);
    cdcaux_block_device_obj_t *self = mp_obj_malloc(cdcaux_block_device_obj_t, type);
    mp_load_method(args[0], MP_QSTR_readblocks, self->readblocks);
    mp_load_method(args[0], MP_QSTR_writeblocks, self->writeblocks);
    mp_load_method(args[0], MP_QSTR_ioctl, self->ioctl);
    return MP_OBJ_FROM_PTR(self);
}

static mp_obj_t cdcaux_block_device_call(const mp_obj_t *method, size_t n_args, const mp_obj_t *args, bool changes) {
    mp_obj_t call[5] = { method[0], method[1] };
    for (size_t i = 0; i < n_args; i++) {
        call[2 + i] = args[i];
    }
    cdcaux_guard_enter();
    if (changes) {
        cdcaux_fs_mark_changed();
    }
    nlr_buf_t nlr;
    if (nlr_push(&nlr) == 0) {
        mp_obj_t result = mp_call_method_n_kw(n_args, 0, call);
        nlr_pop();
        cdcaux_guard_exit();
        return result;
    }
    cdcaux_guard_exit();
    nlr_jump(nlr.ret_val);
}

static mp_obj_t cdcaux_block_device_readblocks(size_t n_args, const mp_obj_t *args) {
    cdcaux_block_device_obj_t *self = MP_OBJ_TO_PTR(args[0]);
    return cdcaux_block_device_call(self->readblocks, n_args - 1, args + 1, false);
}
static MP_DEFINE_CONST_FUN_OBJ_VAR_BETWEEN(cdcaux_block_device_readblocks_obj, 3, 4, cdcaux_block_device_readblocks);

static mp_obj_t cdcaux_block_device_writeblocks(size_t n_args, const mp_obj_t *args) {
    cdcaux_block_device_obj_t *self = MP_OBJ_TO_PTR(args[0]);
    return cdcaux_block_device_call(self->writeblocks, n_args - 1, args + 1, true);
}
static MP_DEFINE_CONST_FUN_OBJ_VAR_BETWEEN(cdcaux_block_device_writeblocks_obj, 3, 4, cdcaux_block_device_writeblocks);

static mp_obj_t cdcaux_block_device_ioctl(mp_obj_t self_in, mp_obj_t op_in, mp_obj_t arg_in) {
    cdcaux_block_device_obj_t *self = MP_OBJ_TO_PTR(self_in);
    mp_obj_t args[2] = { op_in, arg_in };
    bool erase = mp_obj_get_int(op_in) == MP_BLOCKDEV_IOCTL_BLOCK_ERASE;
    return cdcaux_block_device_call(self->ioctl, 2, args, erase);
}
static MP_DEFINE_CONST_FUN_OBJ_3(cdcaux_block_device_ioctl_obj, cdcaux_block_device_ioctl);

static const mp_rom_map_elem_t cdcaux_block_device_locals_table[] = {
    { MP_ROM_QSTR(MP_QSTR_readblocks), MP_ROM_PTR(&cdcaux_block_device_readblocks_obj) },
    { MP_ROM_QSTR(MP_QSTR_writeblocks), MP_ROM_PTR(&cdcaux_block_device_writeblocks_obj) },
    { MP_ROM_QSTR(MP_QSTR_ioctl), MP_ROM_PTR(&cdcaux_block_device_ioctl_obj) },
};
static MP_DEFINE_CONST_DICT(cdcaux_block_device_locals, cdcaux_block_device_locals_table);

MP_DEFINE_CONST_OBJ_TYPE(
    cdcaux_block_device_type,
    MP_QSTR_BlockDevice,
    MP_TYPE_FLAG_NONE,
    make_new, cdcaux_block_device_make_new,
    locals_dict, &cdcaux_block_device_locals
    );

static mp_obj_t cdcaux_claim(mp_obj_t claim_in) {
    cdcaux_claimed = mp_obj_is_true(claim_in);
    if (!cdcaux_claimed) {
        cdcaux_inbox_len = 0;
        cdcaux_schedule();
    }
    return mp_const_none;
}
static MP_DEFINE_CONST_FUN_OBJ_1(cdcaux_claim_obj, cdcaux_claim);

static mp_obj_t cdcaux_connected(void) {
    return mp_obj_new_bool(tud_cdc_n_connected(CDCAUX_ITF));
}
static MP_DEFINE_CONST_FUN_OBJ_0(cdcaux_connected_obj, cdcaux_connected);

static mp_obj_t cdcaux_any(void) {
    mp_usbd_task();
    cdcaux_service();
    return MP_OBJ_NEW_SMALL_INT(cdcaux_inbox_len);
}
static MP_DEFINE_CONST_FUN_OBJ_0(cdcaux_any_obj, cdcaux_any);

static mp_obj_t cdcaux_read(size_t n_args, const mp_obj_t *args) {
    mp_usbd_task();
    cdcaux_service();
    mp_int_t count = cdcaux_inbox_len;
    if (n_args > 0 && args[0] != mp_const_none) {
        count = MIN(count, mp_obj_get_int(args[0]));
    }
    if (count <= 0) {
        return mp_const_none;
    }
    uint8_t *inbox = cdcaux_buffers()->inbox;
    mp_obj_t data = mp_obj_new_bytes(inbox, count);
    memmove(inbox, inbox + count, cdcaux_inbox_len - count);
    cdcaux_inbox_len -= count;
    cdcaux_schedule();
    return data;
}
static MP_DEFINE_CONST_FUN_OBJ_VAR_BETWEEN(cdcaux_read_obj, 0, 1, cdcaux_read);

static mp_obj_t cdcaux_write(mp_obj_t data_in) {
    mp_buffer_info_t bufinfo;
    mp_get_buffer_raise(data_in, &bufinfo, MP_BUFFER_READ);
    cdcaux_guard_enter();
    nlr_buf_t nlr;
    if (nlr_push(&nlr) == 0) {
        size_t written = cdcaux_send(bufinfo.buf, bufinfo.len);
        nlr_pop();
        cdcaux_guard_exit();
        return MP_OBJ_NEW_SMALL_INT(written);
    }
    cdcaux_guard_exit();
    nlr_jump(nlr.ret_val);
}
static MP_DEFINE_CONST_FUN_OBJ_1(cdcaux_write_obj, cdcaux_write);

static const mp_rom_map_elem_t cdcaux_globals_table[] = {
    { MP_ROM_QSTR(MP_QSTR___name__), MP_ROM_QSTR(MP_QSTR_cdcaux) },
    { MP_ROM_QSTR(MP_QSTR_claim), MP_ROM_PTR(&cdcaux_claim_obj) },
    { MP_ROM_QSTR(MP_QSTR_connected), MP_ROM_PTR(&cdcaux_connected_obj) },
    { MP_ROM_QSTR(MP_QSTR_any), MP_ROM_PTR(&cdcaux_any_obj) },
    { MP_ROM_QSTR(MP_QSTR_read), MP_ROM_PTR(&cdcaux_read_obj) },
    { MP_ROM_QSTR(MP_QSTR_write), MP_ROM_PTR(&cdcaux_write_obj) },
    { MP_ROM_QSTR(MP_QSTR_app), MP_ROM_PTR(&cdcaux_app_obj) },
    { MP_ROM_QSTR(MP_QSTR_held), MP_ROM_PTR(&cdcaux_held_obj) },
    { MP_ROM_QSTR(MP_QSTR_release), MP_ROM_PTR(&cdcaux_release_obj) },
    { MP_ROM_QSTR(MP_QSTR_launch), MP_ROM_PTR(&cdcaux_launch_obj) },
    { MP_ROM_QSTR(MP_QSTR_BlockDevice), MP_ROM_PTR(&cdcaux_block_device_type) },
};
static MP_DEFINE_CONST_DICT(cdcaux_globals, cdcaux_globals_table);

const mp_obj_module_t mod_cdcaux = {
    .base = { &mp_type_module },
    .globals = (mp_obj_dict_t *)&cdcaux_globals,
};

MP_REGISTER_MODULE(MP_QSTR_cdcaux, mod_cdcaux);

#else

void cdcaux_soft_reset(void) {
}

#endif
