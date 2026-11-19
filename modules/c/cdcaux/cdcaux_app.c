#include <string.h>

#include "py/runtime.h"
#include "py/mphal.h"
#include "py/mperrno.h"
#include "py/ringbuf.h"
#include "shared/runtime/pyexec.h"
#include "cdcaux.h"

#if MICROPY_HW_USB_CDC_AUX

#define CDCAUX_LEASE_MS (10000)
#define CDCAUX_CTRL_D (0x04)
#define CDCAUX_ID_MAX (48)

static bool app_held = false;
static mp_uint_t app_last_request_ms = 0;
static char app_path[CDCAUX_PATH_MAX];
static char app_resume_path[CDCAUX_PATH_MAX];

static bool app_launch_pending = false;
static char app_launch_path[CDCAUX_PATH_MAX];
static bool app_launch_debug = false;
static bool app_launch_resume = false;

static const char *app_reply_event = NULL;
static char app_reply_id[CDCAUX_ID_MAX];
static bool app_reset_pending = false;

cdcaux_state_t cdcaux_app_state(void) {
    if (app_held) {
        return CDCAUX_STATE_HELD;
    }
    if (app_path[0] != '\0') {
        return CDCAUX_STATE_RUNNING;
    }
    return CDCAUX_STATE_IDLE;
}

const char *cdcaux_app_state_name(void) {
    switch (cdcaux_app_state()) {
        case CDCAUX_STATE_HELD:
            return "held";
        case CDCAUX_STATE_RUNNING:
            return "running";
        default:
            return "idle";
    }
}

const char *cdcaux_app_path(void) {
    return app_path[0] == '\0' ? NULL : app_path;
}

void cdcaux_app_check_writable(const char *path) {
    if (cdcaux_app_state() != CDCAUX_STATE_RUNNING) {
        return;
    }
    size_t app_len = strlen(app_path);
    size_t path_len = strlen(path);
    bool inside = strncmp(path, app_path, app_len) == 0 && (path[app_len] == '\0' || path[app_len] == '/');
    bool ancestor = path_len == 1 || (strncmp(app_path, path, path_len) == 0 && app_path[path_len] == '/');
    if (inside || ancestor) {
        mp_raise_OSError(MP_EBUSY);
    }
}

bool cdcaux_app_reset_pending(void) {
    return app_reset_pending;
}

void cdcaux_app_touch(void) {
    app_last_request_ms = mp_hal_ticks_ms();
}

static void cdcaux_app_set_held(bool held) {
    if (app_held != held) {
        app_held = held;
        cdcaux_fs_state_changed();
    }
}

static void cdcaux_app_copy_path(char *dest, const char *src) {
    size_t len = strlen(src);
    if (len >= CDCAUX_PATH_MAX) {
        mp_raise_OSError(CDCAUX_ENAMETOOLONG);
    }
    memcpy(dest, src, len + 1);
}

static void cdcaux_app_request_reset(void) {
    app_reset_pending = true;
    pyexec_mode_kind = PYEXEC_MODE_FRIENDLY_REPL;
    if (nlr_get_abort() != NULL) {
        mp_sched_vm_abort();
        cdcaux_schedule();
    } else {
        ringbuf_put(&stdin_ringbuf, CDCAUX_CTRL_D);
    }
}

static void cdcaux_app_reply_state(const char *event, mp_obj_t id, const char *state) {
    cdcaux_reply_t reply;
    cdcaux_reply_begin(&reply, event, id);
    mp_printf(&reply.print, ", \"state\": \"%s\"", state);
    cdcaux_reply_send(&reply, NULL, 0);
}

static void cdcaux_app_defer_reply(const char *event, mp_obj_t id) {
    vstr_t vstr;
    mp_print_t print;
    vstr_init_print(&vstr, CDCAUX_ID_MAX, &print);
    mp_obj_print_helper(&print, id, PRINT_JSON);
    if (vstr.len < CDCAUX_ID_MAX) {
        memcpy(app_reply_id, vstr.buf, vstr.len);
        app_reply_id[vstr.len] = '\0';
    } else {
        strcpy(app_reply_id, "null");
    }
    vstr_clear(&vstr);
    app_reply_event = event;
}

static void cdcaux_app_hold(const char *event, mp_obj_t id) {
    if (app_held) {
        cdcaux_app_reply_state(event, id, "held");
        return;
    }
    strcpy(app_resume_path, app_path);
    cdcaux_app_set_held(true);
    if (nlr_get_abort() == NULL && app_path[0] == '\0') {
        cdcaux_app_reply_state(event, id, "held");
        return;
    }
    cdcaux_app_defer_reply(event, id);
    cdcaux_app_request_reset();
}

static void cdcaux_app_unlock(mp_obj_t request, mp_obj_t id) {
    bool resume = cdcaux_get_bool(request, MP_QSTR_resume) && app_held && app_resume_path[0] != '\0';
    if (resume) {
        strcpy(app_launch_path, app_resume_path);
        app_launch_debug = false;
        app_launch_resume = true;
        app_launch_pending = true;
    }
    cdcaux_app_set_held(false);
    cdcaux_app_reply_state("fs.unlock", id, resume ? "running" : cdcaux_app_state_name());
}

static void cdcaux_app_run(mp_obj_t request, mp_obj_t id) {
    const char *path = cdcaux_get_str(request, MP_QSTR_path);
    if (path[0] != '/') {
        mp_raise_OSError(MP_EINVAL);
    }
    cdcaux_app_copy_path(app_launch_path, path);
    app_launch_debug = cdcaux_get_bool(request, MP_QSTR_debug);
    app_launch_resume = false;
    app_launch_pending = true;
    cdcaux_app_set_held(false);
    cdcaux_reply_ok("app.run", id);
    cdcaux_app_request_reset();
}

static bool cdcaux_app_dispatch(const char *cmd, mp_obj_t request, mp_obj_t id, const uint8_t *payload, size_t payload_len) {
    (void)payload;
    (void)payload_len;
    if (strcmp(cmd, "fs.lock") == 0) {
        cdcaux_app_hold("fs.lock", id);
    } else if (strcmp(cmd, "app.stop") == 0) {
        cdcaux_app_hold("app.stop", id);
    } else if (strcmp(cmd, "fs.unlock") == 0) {
        cdcaux_app_unlock(request, id);
    } else if (strcmp(cmd, "app.run") == 0) {
        cdcaux_app_run(request, id);
    } else {
        return false;
    }
    return true;
}

static void cdcaux_app_service(bool connected) {
    if (app_held && (mp_uint_t)(mp_hal_ticks_ms() - app_last_request_ms) > CDCAUX_LEASE_MS) {
        cdcaux_app_set_held(false);
    }
    if (app_reply_event != NULL && connected && !app_reset_pending && cdcaux_fs_ready()) {
        const char *event = app_reply_event;
        app_reply_event = NULL;
        cdcaux_reply_t reply;
        cdcaux_reply_begin(&reply, event, MP_OBJ_NULL);
        mp_printf(&reply.print, ", \"id\": %s, \"state\": \"%s\"", app_reply_id, cdcaux_app_state_name());
        cdcaux_reply_send(&reply, NULL, 0);
    }
}

static void cdcaux_app_disconnected(void) {
    app_reply_event = NULL;
    cdcaux_app_set_held(false);
}

static void cdcaux_app_soft_reset(void) {
    app_reset_pending = false;
    app_path[0] = '\0';
    app_last_request_ms = mp_hal_ticks_ms();
}

const cdcaux_role_t cdcaux_app_role = {
    .prefix = "app.",
    .dispatch = cdcaux_app_dispatch,
    .service = cdcaux_app_service,
    .disconnected = cdcaux_app_disconnected,
    .soft_reset = cdcaux_app_soft_reset,
};

static mp_obj_t cdcaux_app(mp_obj_t path_in) {
    if (path_in == mp_const_none) {
        app_path[0] = '\0';
    } else {
        cdcaux_app_copy_path(app_path, mp_obj_str_get_str(path_in));
    }
    cdcaux_fs_state_changed();
    cdcaux_service();
    return mp_const_none;
}
MP_DEFINE_CONST_FUN_OBJ_1(cdcaux_app_obj, cdcaux_app);

static mp_obj_t cdcaux_held(void) {
    cdcaux_service();
    return mp_obj_new_bool(app_held);
}
MP_DEFINE_CONST_FUN_OBJ_0(cdcaux_held_obj, cdcaux_held);

static mp_obj_t cdcaux_release(void) {
    cdcaux_app_set_held(false);
    cdcaux_service();
    return mp_const_none;
}
MP_DEFINE_CONST_FUN_OBJ_0(cdcaux_release_obj, cdcaux_release);

static mp_obj_t cdcaux_launch(void) {
    cdcaux_service();
    if (!app_launch_pending) {
        return mp_const_none;
    }
    app_launch_pending = false;
    mp_obj_t items[3] = {
        mp_obj_new_str(app_launch_path, strlen(app_launch_path)),
        mp_obj_new_bool(app_launch_debug),
        mp_obj_new_bool(app_launch_resume),
    };
    return mp_obj_new_tuple(3, items);
}
MP_DEFINE_CONST_FUN_OBJ_0(cdcaux_launch_obj, cdcaux_launch);

#endif
