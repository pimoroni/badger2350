#include <string.h>

#include "py/runtime.h"
#include "py/mperrno.h"
#include "py/objtuple.h"
#include "py/stream.h"
#include "extmod/vfs.h"
#include "shared/runtime/softtimer.h"
#include "cdcaux.h"

#if MICROPY_HW_USB_CDC_AUX

#define CDCAUX_FS_VERSION (1)
#define CDCAUX_LIST_LIMIT (64)
#define CDCAUX_LIST_LIMIT_MAX (256)
#define CDCAUX_CHANGE_DELAY_MS (100)

MP_REGISTER_ROOT_POINTER(mp_obj_t cdcaux_fs_files[2]);
MP_REGISTER_ROOT_POINTER(mp_obj_t cdcaux_fs_targets[2]);

static mp_uint_t fs_lengths[CDCAUX_HANDLES];
static bool fs_active = false;
static bool fs_watch = false;
static bool fs_temps_cleaned = false;
static volatile bool fs_changed_dirty = false;
static volatile bool fs_changed_ready = false;
static volatile bool fs_timer_armed = false;
static bool fs_timer_initialised = false;
static bool fs_state_dirty = false;
static soft_timer_entry_t fs_timer;

typedef void (*cdcaux_fs_handler_t)(mp_obj_t request, mp_obj_t id, const uint8_t *payload, size_t payload_len);

bool cdcaux_fs_ready(void) {
    for (mp_vfs_mount_t *mount = MP_STATE_VM(vfs_mount_table); mount != NULL; mount = mount->next) {
        if (mount->len == 1) {
            return true;
        }
    }
    return false;
}

static mp_obj_t fs_str(const char *str) {
    return mp_obj_new_str(str, strlen(str));
}

static mp_obj_t fs_path(mp_obj_t request, qstr key, const char **path_out, bool writable) {
    const char *path = cdcaux_get_str(request, key);
    size_t len = strlen(path);
    if (len >= CDCAUX_PATH_MAX) {
        mp_raise_OSError(CDCAUX_ENAMETOOLONG);
    }
    if (path[0] != '/' || (len > 1 && path[len - 1] == '/')) {
        mp_raise_OSError(MP_EINVAL);
    }
    const char *segment = path + 1;
    while (len > 1 && *segment != '\0') {
        const char *end = strchr(segment, '/');
        size_t segment_len = end == NULL ? strlen(segment) : (size_t)(end - segment);
        if (segment_len == 0
            || (segment_len == 1 && segment[0] == '.')
            || (segment_len == 2 && segment[0] == '.' && segment[1] == '.')) {
            mp_raise_OSError(MP_EINVAL);
        }
        segment += segment_len + (end == NULL ? 0 : 1);
    }
    if (len == 1) {
        if (!cdcaux_fs_ready()) {
            mp_raise_OSError(MP_EINVAL);
        }
    } else {
        const char *rest;
        mp_vfs_mount_t *mount = mp_vfs_lookup_path(path, &rest);
        if (mount == MP_VFS_NONE || mount == MP_VFS_ROOT) {
            mp_raise_OSError(MP_EINVAL);
        }
        if (writable && mount->len != 1) {
            mp_raise_OSError(MP_EROFS);
        }
    }
    *path_out = path;
    return cdcaux_get(request, key);
}

static mp_obj_t fs_join(const char *parent, const char *name) {
    vstr_t vstr;
    vstr_init(&vstr, strlen(parent) + strlen(name) + 2);
    vstr_add_str(&vstr, parent);
    if (strcmp(parent, "/") != 0) {
        vstr_add_char(&vstr, '/');
    }
    vstr_add_str(&vstr, name);
    return mp_obj_new_str_from_vstr(&vstr);
}

static mp_obj_t fs_parent(const char *path) {
    const char *slash = strrchr(path, '/');
    if (slash == path) {
        return fs_str("/");
    }
    return mp_obj_new_str(path, slash - path);
}

static mp_obj_t fs_temp_path(size_t index) {
    vstr_t vstr;
    vstr_init(&vstr, 16);
    vstr_printf(&vstr, "/.fs-tmp-%u", (unsigned int)(index + 1));
    return mp_obj_new_str_from_vstr(&vstr);
}

static mp_obj_t *fs_stat_items(mp_obj_t stat) {
    size_t len;
    mp_obj_t *items;
    mp_obj_tuple_get(stat, &len, &items);
    return items;
}

static bool fs_is_dir(mp_obj_t stat) {
    return (mp_obj_get_int(fs_stat_items(stat)[0]) & MP_S_IFDIR) != 0;
}

static mp_obj_t fs_stat_maybe(mp_obj_t path) {
    nlr_buf_t nlr;
    if (nlr_push(&nlr) == 0) {
        mp_obj_t stat = mp_vfs_stat(path);
        nlr_pop();
        return stat;
    }
    if (cdcaux_exception_errno(MP_OBJ_FROM_PTR(nlr.ret_val)) == MP_ENOENT) {
        return MP_OBJ_NULL;
    }
    nlr_jump(nlr.ret_val);
}

static void fs_quietly(mp_obj_t (*fn)(mp_obj_t), mp_obj_t arg) {
    nlr_buf_t nlr;
    if (nlr_push(&nlr) == 0) {
        fn(arg);
        nlr_pop();
    }
}

static mp_obj_t fs_open(mp_obj_t path, const char *mode) {
    mp_obj_t args[2] = { path, fs_str(mode) };
    return mp_vfs_open(2, args, (mp_map_t *)&mp_const_empty_map);
}

static void fs_check(int err) {
    if (err != 0) {
        mp_raise_OSError(err);
    }
}

static mp_uint_t fs_read_into(mp_obj_t file, uint8_t *buf, mp_uint_t len) {
    int err = 0;
    mp_uint_t count = mp_stream_rw(file, buf, len, &err, MP_STREAM_RW_READ);
    fs_check(err);
    return count;
}

static void fs_print_entry_type(const mp_print_t *print, bool is_dir) {
    mp_printf(print, "\"type\": \"%s\"", is_dir ? "dir" : "file");
}

static void fs_print_dict_str(const mp_print_t *print, const char *key, const char *value) {
    mp_printf(print, ", \"%s\": ", key);
    if (value == NULL) {
        mp_print_str(print, "null");
    } else {
        cdcaux_print_str(print, value);
    }
}

static void fs_info(mp_obj_t request, mp_obj_t id, const uint8_t *payload, size_t payload_len) {
    mp_obj_t *items = fs_stat_items(mp_vfs_statvfs(fs_str("/")));
    mp_int_t blocks = mp_obj_get_int(items[2]);
    cdcaux_reply_t reply;
    cdcaux_reply_begin(&reply, "fs.info", id);
    mp_printf(&reply.print, ", \"version\": %d, \"block_size\": %d, \"block_count\": %d, \"blocks_used\": %d",
        CDCAUX_FS_VERSION, (int)mp_obj_get_int(items[0]), (int)blocks, (int)(blocks - mp_obj_get_int(items[3])));
    mp_printf(&reply.print, ", \"name_max\": %d, \"chunk\": %d, \"handles\": %d",
        (int)mp_obj_get_int(items[9]), CDCAUX_CHUNK, CDCAUX_HANDLES);
    fs_print_dict_str(&reply.print, "state", cdcaux_app_state_name());
    fs_print_dict_str(&reply.print, "app", cdcaux_app_path());
    cdcaux_reply_send(&reply, NULL, 0);
}

static void fs_stat(mp_obj_t request, mp_obj_t id, const uint8_t *payload, size_t payload_len) {
    const char *path;
    mp_obj_t stat = mp_vfs_stat(fs_path(request, MP_QSTR_path, &path, false));
    mp_obj_t *items = fs_stat_items(stat);
    bool is_dir = fs_is_dir(stat);
    cdcaux_reply_t reply;
    cdcaux_reply_begin(&reply, "fs.stat", id);
    mp_print_str(&reply.print, ", ");
    fs_print_entry_type(&reply.print, is_dir);
    mp_printf(&reply.print, ", \"size\": %d, \"mtime\": %d",
        is_dir ? 0 : (int)mp_obj_get_int(items[6]), (int)mp_obj_get_int(items[8]));
    cdcaux_reply_send(&reply, NULL, 0);
}

static void fs_list(mp_obj_t request, mp_obj_t id, const uint8_t *payload, size_t payload_len) {
    const char *path;
    mp_obj_t path_obj = fs_path(request, MP_QSTR_path, &path, false);
    mp_int_t offset = MAX(0, cdcaux_get_int(request, MP_QSTR_offset, 0));
    mp_int_t limit = MIN(CDCAUX_LIST_LIMIT_MAX, MAX(1, cdcaux_get_int(request, MP_QSTR_limit, CDCAUX_LIST_LIMIT)));

    mp_obj_t iter = mp_vfs_ilistdir(1, &path_obj);
    cdcaux_reply_t reply;
    cdcaux_reply_begin(&reply, "fs.list", id);
    mp_print_str(&reply.print, ", \"entries\": [");

    mp_int_t index = 0;
    mp_int_t count = 0;
    bool more = false;
    mp_obj_t entry;
    while ((entry = mp_iternext(iter)) != MP_OBJ_STOP_ITERATION) {
        if (index++ < offset) {
            continue;
        }
        if (count == limit) {
            more = true;
            continue;
        }
        size_t entry_len;
        mp_obj_t *entry_items;
        mp_obj_tuple_get(entry, &entry_len, &entry_items);
        const char *name = mp_obj_str_get_str(entry_items[0]);
        bool is_dir = (mp_obj_get_int(entry_items[1]) & MP_S_IFDIR) != 0;
        mp_obj_t *stat_items = fs_stat_items(mp_vfs_stat(fs_join(path, name)));
        mp_print_str(&reply.print, count == 0 ? "{\"name\": " : ", {\"name\": ");
        cdcaux_print_str(&reply.print, name);
        mp_print_str(&reply.print, ", ");
        fs_print_entry_type(&reply.print, is_dir);
        mp_printf(&reply.print, ", \"size\": %d, \"mtime\": %d}",
            is_dir ? 0 : (int)mp_obj_get_int(stat_items[6]), (int)mp_obj_get_int(stat_items[8]));
        count++;
    }
    mp_printf(&reply.print, "], \"more\": %s", more ? "true" : "false");
    cdcaux_reply_send(&reply, NULL, 0);
}

static void fs_read(mp_obj_t request, mp_obj_t id, const uint8_t *payload, size_t payload_len) {
    const char *path;
    mp_obj_t path_obj = fs_path(request, MP_QSTR_path, &path, false);
    mp_int_t offset = cdcaux_get_int(request, MP_QSTR_offset, 0);
    mp_int_t length = cdcaux_get_int(request, MP_QSTR_length, CDCAUX_CHUNK);
    if (offset < 0 || length < 0) {
        mp_raise_OSError(MP_EINVAL);
    }
    length = MIN(length, CDCAUX_CHUNK);

    mp_obj_t stat = mp_vfs_stat(path_obj);
    if (fs_is_dir(stat)) {
        mp_raise_OSError(MP_EISDIR);
    }
    mp_int_t size = mp_obj_get_int(fs_stat_items(stat)[6]);

    uint8_t *buf = m_new(uint8_t, MAX(length, 1));
    mp_uint_t count = 0;
    mp_obj_t file = fs_open(path_obj, "rb");
    nlr_buf_t nlr;
    if (nlr_push(&nlr) == 0) {
        int err = 0;
        if (mp_stream_seek(file, offset, MP_SEEK_SET, &err) == (mp_off_t)-1) {
            fs_check(err);
        }
        count = fs_read_into(file, buf, length);
        nlr_pop();
    } else {
        fs_quietly(mp_stream_close, file);
        nlr_jump(nlr.ret_val);
    }
    mp_stream_close(file);

    cdcaux_reply_t reply;
    cdcaux_reply_begin(&reply, "fs.read", id);
    mp_printf(&reply.print, ", \"eof\": %s", offset + (mp_int_t)count >= size ? "true" : "false");
    cdcaux_reply_send(&reply, buf, count);
    m_del(uint8_t, buf, MAX(length, 1));
}

static void fs_hash(mp_obj_t request, mp_obj_t id, const uint8_t *payload, size_t payload_len) {
    const char *path;
    mp_obj_t path_obj = fs_path(request, MP_QSTR_path, &path, false);
    mp_obj_t stat = mp_vfs_stat(path_obj);
    if (fs_is_dir(stat)) {
        mp_raise_OSError(MP_EISDIR);
    }

    mp_obj_t hashlib = mp_import_name(MP_QSTR_hashlib, mp_const_none, MP_OBJ_NEW_SMALL_INT(0));
    mp_obj_t hasher = mp_call_function_0(mp_load_attr(hashlib, MP_QSTR_sha256));
    mp_obj_t update = mp_load_attr(hasher, MP_QSTR_update);

    uint8_t *buf = m_new(uint8_t, CDCAUX_CHUNK);
    mp_uint_t total = 0;
    mp_obj_t file = fs_open(path_obj, "rb");
    nlr_buf_t nlr;
    if (nlr_push(&nlr) == 0) {
        mp_uint_t count;
        while ((count = fs_read_into(file, buf, CDCAUX_CHUNK)) > 0) {
            mp_call_function_1(update, mp_obj_new_bytearray_by_ref(count, buf));
            total += count;
        }
        nlr_pop();
    } else {
        fs_quietly(mp_stream_close, file);
        nlr_jump(nlr.ret_val);
    }
    mp_stream_close(file);
    m_del(uint8_t, buf, CDCAUX_CHUNK);

    mp_buffer_info_t digest;
    mp_get_buffer_raise(mp_call_function_0(mp_load_attr(hasher, MP_QSTR_digest)), &digest, MP_BUFFER_READ);
    cdcaux_reply_t reply;
    cdcaux_reply_begin(&reply, "fs.hash", id);
    mp_print_str(&reply.print, ", \"sha256\": \"");
    for (size_t i = 0; i < digest.len; i++) {
        mp_printf(&reply.print, "%02x", ((const uint8_t *)digest.buf)[i]);
    }
    mp_printf(&reply.print, "\", \"size\": %u", (unsigned int)total);
    cdcaux_reply_send(&reply, NULL, 0);
}

static void fs_mkdir(mp_obj_t request, mp_obj_t id, const uint8_t *payload, size_t payload_len) {
    const char *path;
    mp_obj_t path_obj = fs_path(request, MP_QSTR_path, &path, true);
    cdcaux_app_check_writable(path);
    if (!cdcaux_get_bool(request, MP_QSTR_parents)) {
        mp_vfs_mkdir(path_obj);
        cdcaux_reply_ok("fs.mkdir", id);
        return;
    }
    size_t len = strlen(path);
    for (size_t i = 1; i <= len; i++) {
        if (path[i] != '/' && path[i] != '\0') {
            continue;
        }
        mp_obj_t prefix = mp_obj_new_str(path, i);
        mp_obj_t stat = fs_stat_maybe(prefix);
        if (stat == MP_OBJ_NULL) {
            mp_vfs_mkdir(prefix);
        } else if (!fs_is_dir(stat)) {
            mp_raise_OSError(MP_ENOTDIR);
        }
    }
    cdcaux_reply_ok("fs.mkdir", id);
}

static void fs_remove_tree(mp_obj_t path_obj, bool recursive) {
    mp_obj_t stat = mp_vfs_stat(path_obj);
    if (!fs_is_dir(stat)) {
        mp_vfs_remove(path_obj);
        return;
    }
    if (recursive) {
        const char *path = mp_obj_str_get_str(path_obj);
        mp_obj_t names = mp_obj_new_list(0, NULL);
        mp_obj_t iter = mp_vfs_ilistdir(1, &path_obj);
        mp_obj_t entry;
        while ((entry = mp_iternext(iter)) != MP_OBJ_STOP_ITERATION) {
            size_t entry_len;
            mp_obj_t *entry_items;
            mp_obj_tuple_get(entry, &entry_len, &entry_items);
            mp_obj_list_append(names, entry_items[0]);
        }
        size_t count;
        mp_obj_t *items;
        mp_obj_list_get(names, &count, &items);
        for (size_t i = 0; i < count; i++) {
            fs_remove_tree(fs_join(path, mp_obj_str_get_str(items[i])), true);
        }
    }
    mp_vfs_rmdir(path_obj);
}

static void fs_remove(mp_obj_t request, mp_obj_t id, const uint8_t *payload, size_t payload_len) {
    const char *path;
    mp_obj_t path_obj = fs_path(request, MP_QSTR_path, &path, true);
    if (strcmp(path, "/") == 0) {
        mp_raise_OSError(MP_EINVAL);
    }
    cdcaux_app_check_writable(path);
    fs_remove_tree(path_obj, cdcaux_get_bool(request, MP_QSTR_recursive));
    cdcaux_reply_ok("fs.remove", id);
}

static void fs_rename(mp_obj_t request, mp_obj_t id, const uint8_t *payload, size_t payload_len) {
    const char *from;
    const char *to;
    mp_obj_t from_obj = fs_path(request, MP_QSTR_from, &from, true);
    mp_obj_t to_obj = fs_path(request, MP_QSTR_to, &to, true);
    cdcaux_app_check_writable(from);
    cdcaux_app_check_writable(to);
    mp_vfs_rename(from_obj, to_obj);
    cdcaux_reply_ok("fs.rename", id);
}

static size_t fs_handle_index(mp_obj_t request) {
    mp_int_t handle = cdcaux_get_int(request, MP_QSTR_handle, 0);
    if (handle < 1 || handle > CDCAUX_HANDLES || MP_STATE_VM(cdcaux_fs_files)[handle - 1] == MP_OBJ_NULL) {
        mp_raise_OSError(MP_EBADF);
    }
    return handle - 1;
}

static void fs_release_handle(size_t index, bool discard) {
    mp_obj_t file = MP_STATE_VM(cdcaux_fs_files)[index];
    MP_STATE_VM(cdcaux_fs_files)[index] = MP_OBJ_NULL;
    MP_STATE_VM(cdcaux_fs_targets)[index] = MP_OBJ_NULL;
    if (file != MP_OBJ_NULL) {
        fs_quietly(mp_stream_close, file);
    }
    if (discard) {
        fs_quietly(mp_vfs_remove, fs_temp_path(index));
    }
}

static void fs_open_handle(mp_obj_t request, mp_obj_t id, const uint8_t *payload, size_t payload_len) {
    const char *path;
    mp_obj_t path_obj = fs_path(request, MP_QSTR_path, &path, true);
    cdcaux_app_check_writable(path);

    mp_obj_t stat = fs_stat_maybe(path_obj);
    if (stat != MP_OBJ_NULL && fs_is_dir(stat)) {
        mp_raise_OSError(MP_EISDIR);
    }
    if (stat != MP_OBJ_NULL && cdcaux_get_bool(request, MP_QSTR_exclusive)) {
        mp_raise_OSError(MP_EEXIST);
    }
    mp_obj_t parent = fs_stat_maybe(fs_parent(path));
    if (parent == MP_OBJ_NULL) {
        mp_raise_OSError(MP_ENOENT);
    }
    if (!fs_is_dir(parent)) {
        mp_raise_OSError(MP_ENOTDIR);
    }

    mp_int_t size = cdcaux_get_int(request, MP_QSTR_size, 0);
    if (size > 0) {
        mp_obj_t *items = fs_stat_items(mp_vfs_statvfs(fs_str("/")));
        if ((mp_uint_t)size > (mp_uint_t)mp_obj_get_int(items[0]) * (mp_uint_t)mp_obj_get_int(items[3])) {
            mp_raise_OSError(MP_ENOSPC);
        }
    }

    size_t index = 0;
    while (index < CDCAUX_HANDLES && MP_STATE_VM(cdcaux_fs_files)[index] != MP_OBJ_NULL) {
        index++;
    }
    if (index == CDCAUX_HANDLES) {
        mp_raise_OSError(MP_EBUSY);
    }

    MP_STATE_VM(cdcaux_fs_files)[index] = fs_open(fs_temp_path(index), "wb");
    MP_STATE_VM(cdcaux_fs_targets)[index] = path_obj;
    fs_lengths[index] = 0;

    cdcaux_reply_t reply;
    cdcaux_reply_begin(&reply, "fs.open", id);
    mp_printf(&reply.print, ", \"handle\": %u", (unsigned int)(index + 1));
    cdcaux_reply_send(&reply, NULL, 0);
}

static void fs_write(mp_obj_t request, mp_obj_t id, const uint8_t *payload, size_t payload_len) {
    size_t index = fs_handle_index(request);
    if (cdcaux_get_int(request, MP_QSTR_offset, -1) != (mp_int_t)fs_lengths[index]) {
        mp_raise_OSError(MP_EINVAL);
    }
    int err = 0;
    mp_uint_t written = 0;
    if (payload_len > 0) {
        written = mp_stream_rw(MP_STATE_VM(cdcaux_fs_files)[index], (void *)payload, payload_len, &err, MP_STREAM_RW_WRITE);
        fs_check(err);
    }
    fs_lengths[index] += written;

    cdcaux_reply_t reply;
    cdcaux_reply_begin(&reply, "fs.write", id);
    mp_printf(&reply.print, ", \"written\": %u", (unsigned int)written);
    cdcaux_reply_send(&reply, NULL, 0);
}

static void fs_close_handle(mp_obj_t request, mp_obj_t id, const uint8_t *payload, size_t payload_len) {
    size_t index = fs_handle_index(request);
    mp_obj_t file = MP_STATE_VM(cdcaux_fs_files)[index];
    mp_obj_t target = MP_STATE_VM(cdcaux_fs_targets)[index];
    mp_uint_t length = fs_lengths[index];

    nlr_buf_t nlr;
    if (nlr_push(&nlr) == 0) {
        cdcaux_app_check_writable(mp_obj_str_get_str(target));
        mp_stream_close(file);
        MP_STATE_VM(cdcaux_fs_files)[index] = MP_OBJ_NULL;
        mp_vfs_rename(fs_temp_path(index), target);
        MP_STATE_VM(cdcaux_fs_targets)[index] = MP_OBJ_NULL;
        nlr_pop();
    } else {
        fs_release_handle(index, true);
        nlr_jump(nlr.ret_val);
    }

    cdcaux_reply_t reply;
    cdcaux_reply_begin(&reply, "fs.close", id);
    mp_printf(&reply.print, ", \"size\": %u", (unsigned int)length);
    cdcaux_reply_send(&reply, NULL, 0);
}

static void fs_abort_handle(mp_obj_t request, mp_obj_t id, const uint8_t *payload, size_t payload_len) {
    fs_release_handle(fs_handle_index(request), true);
    cdcaux_reply_ok("fs.abort", id);
}

static void fs_watch_cmd(mp_obj_t request, mp_obj_t id, const uint8_t *payload, size_t payload_len) {
    fs_watch = cdcaux_get_bool(request, MP_QSTR_enable);
    cdcaux_reply_ok("fs.watch", id);
}

static const struct {
    const char *name;
    cdcaux_fs_handler_t handler;
} fs_handlers[] = {
    { "fs.info", fs_info },
    { "fs.stat", fs_stat },
    { "fs.list", fs_list },
    { "fs.read", fs_read },
    { "fs.hash", fs_hash },
    { "fs.mkdir", fs_mkdir },
    { "fs.remove", fs_remove },
    { "fs.rename", fs_rename },
    { "fs.open", fs_open_handle },
    { "fs.write", fs_write },
    { "fs.close", fs_close_handle },
    { "fs.abort", fs_abort_handle },
    { "fs.watch", fs_watch_cmd },
};

static void fs_clean_temps(void) {
    if (fs_temps_cleaned) {
        return;
    }
    fs_temps_cleaned = true;
    for (size_t index = 0; index < CDCAUX_HANDLES; index++) {
        if (MP_STATE_VM(cdcaux_fs_files)[index] == MP_OBJ_NULL) {
            fs_quietly(mp_vfs_remove, fs_temp_path(index));
        }
    }
}

static bool cdcaux_fs_dispatch(const char *cmd, mp_obj_t request, mp_obj_t id, const uint8_t *payload, size_t payload_len) {
    for (size_t i = 0; i < MP_ARRAY_SIZE(fs_handlers); i++) {
        if (strcmp(cmd, fs_handlers[i].name) != 0) {
            continue;
        }
        fs_active = true;
        nlr_buf_t nlr;
        if (nlr_push(&nlr) == 0) {
            fs_clean_temps();
            fs_handlers[i].handler(request, id, payload, payload_len);
            nlr_pop();
            fs_active = false;
            return true;
        }
        fs_active = false;
        nlr_jump(nlr.ret_val);
    }
    return false;
}

static void fs_timer_callback(soft_timer_entry_t *entry) {
    (void)entry;
    fs_timer_armed = false;
    fs_changed_ready = true;
    cdcaux_schedule();
}

void cdcaux_fs_mark_changed(void) {
    if (fs_active) {
        return;
    }
    fs_changed_dirty = true;
    if (fs_timer_armed) {
        return;
    }
    if (!fs_timer_initialised) {
        soft_timer_static_init(&fs_timer, SOFT_TIMER_MODE_ONE_SHOT, 0, fs_timer_callback);
        fs_timer_initialised = true;
    }
    fs_timer_armed = true;
    soft_timer_insert(&fs_timer, CDCAUX_CHANGE_DELAY_MS);
}

void cdcaux_fs_state_changed(void) {
    fs_state_dirty = true;
    cdcaux_schedule();
}

static void cdcaux_fs_service(bool connected) {
    if (fs_changed_ready) {
        fs_changed_ready = false;
        if (fs_changed_dirty) {
            fs_changed_dirty = false;
            if (fs_watch && connected) {
                cdcaux_reply_ok("fs.changed", MP_OBJ_NULL);
            }
        }
    }
    if (fs_state_dirty) {
        fs_state_dirty = false;
        if (fs_watch && connected) {
            cdcaux_reply_t reply;
            cdcaux_reply_begin(&reply, "fs.state", MP_OBJ_NULL);
            fs_print_dict_str(&reply.print, "state", cdcaux_app_state_name());
            fs_print_dict_str(&reply.print, "app", cdcaux_app_path());
            cdcaux_reply_send(&reply, NULL, 0);
        }
    }
}

static void cdcaux_fs_disconnected(void) {
    fs_watch = false;
    if (!cdcaux_fs_ready()) {
        return;
    }
    fs_active = true;
    for (size_t index = 0; index < CDCAUX_HANDLES; index++) {
        if (MP_STATE_VM(cdcaux_fs_files)[index] != MP_OBJ_NULL) {
            fs_release_handle(index, true);
        }
    }
    fs_active = false;
}

static void cdcaux_fs_soft_reset(void) {
    fs_active = false;
    fs_temps_cleaned = false;
    fs_changed_dirty = false;
    fs_changed_ready = false;
    fs_state_dirty = true;
    for (size_t index = 0; index < CDCAUX_HANDLES; index++) {
        MP_STATE_VM(cdcaux_fs_files)[index] = MP_OBJ_NULL;
        MP_STATE_VM(cdcaux_fs_targets)[index] = MP_OBJ_NULL;
    }
}

const cdcaux_role_t cdcaux_fs_role = {
    .prefix = "fs.",
    .dispatch = cdcaux_fs_dispatch,
    .service = cdcaux_fs_service,
    .disconnected = cdcaux_fs_disconnected,
    .soft_reset = cdcaux_fs_soft_reset,
};

#endif
