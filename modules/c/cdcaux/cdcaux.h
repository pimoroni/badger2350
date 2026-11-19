#ifndef CDCAUX_H
#define CDCAUX_H

#include "py/runtime.h"

#define CDCAUX_CHUNK (4096)
#define CDCAUX_HANDLES (2)
#define CDCAUX_PATH_MAX (256)

#define CDCAUX_ENOTEMPTY (39)
#define CDCAUX_ENAMETOOLONG (36)
#define CDCAUX_ECORRUPT (84)

typedef enum {
    CDCAUX_STATE_IDLE,
    CDCAUX_STATE_RUNNING,
    CDCAUX_STATE_HELD,
} cdcaux_state_t;

typedef struct _cdcaux_role_t {
    const char *prefix;
    bool (*dispatch)(const char *cmd, mp_obj_t request, mp_obj_t id, const uint8_t *payload, size_t payload_len);
    void (*service)(bool connected);
    void (*disconnected)(void);
    void (*soft_reset)(void);
} cdcaux_role_t;

typedef struct _cdcaux_reply_t {
    vstr_t vstr;
    mp_print_t print;
} cdcaux_reply_t;

void cdcaux_reply_begin(cdcaux_reply_t *reply, const char *event, mp_obj_t id);
void cdcaux_reply_send(cdcaux_reply_t *reply, const uint8_t *payload, size_t payload_len);
void cdcaux_reply_ok(const char *event, mp_obj_t id);
void cdcaux_print_str(const mp_print_t *print, const char *str);

mp_obj_t cdcaux_get(mp_obj_t request, qstr key);
const char *cdcaux_get_str(mp_obj_t request, qstr key);
mp_int_t cdcaux_get_int(mp_obj_t request, qstr key, mp_int_t default_value);
bool cdcaux_get_bool(mp_obj_t request, qstr key);

void cdcaux_schedule(void);
void cdcaux_service(void);
void cdcaux_soft_reset(void);
mp_int_t cdcaux_exception_errno(mp_obj_t exc);

cdcaux_state_t cdcaux_app_state(void);
const char *cdcaux_app_path(void);
const char *cdcaux_app_state_name(void);
void cdcaux_app_check_writable(const char *path);
void cdcaux_app_touch(void);
bool cdcaux_app_reset_pending(void);

bool cdcaux_fs_ready(void);
void cdcaux_fs_mark_changed(void);
void cdcaux_fs_state_changed(void);

extern const mp_obj_type_t cdcaux_block_device_type;
extern const cdcaux_role_t cdcaux_app_role;
extern const cdcaux_role_t cdcaux_fs_role;

MP_DECLARE_CONST_FUN_OBJ_1(cdcaux_app_obj);
MP_DECLARE_CONST_FUN_OBJ_0(cdcaux_held_obj);
MP_DECLARE_CONST_FUN_OBJ_0(cdcaux_release_obj);
MP_DECLARE_CONST_FUN_OBJ_0(cdcaux_launch_obj);

#endif
