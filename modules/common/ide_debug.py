import json
import sys
import time

import cdcaux

MAX_STACK = 32
MAX_REPR = 120
MAX_CHILDREN = 100
INIT_TIMEOUT_MS = 2000

_breakpoints = {}
_mode = "run"
_step_frame = None
_rx = b""
_refs = []
_stopped_frames = []
_resume = False
_initialised = False


def _send(message):
    cdcaux.write(json.dumps(message) + "\n")


def _is_user_file(filename):
    return filename.startswith("/") and not filename.startswith("/.frozen")


def _frame_file(frame):
    return frame.f_code.co_filename


def _stack(frame):
    frames = []
    while frame is not None and len(frames) < MAX_STACK:
        frames.append(frame)
        frame = frame.f_back
    return frames


def _short_repr(value):
    try:
        text = repr(value)
    except Exception:  # noqa: BLE001
        text = "<" + type(value).__name__ + ">"
    if len(text) > MAX_REPR:
        text = text[:MAX_REPR - 3] + "..."
    return text


def _has_children(value):
    if isinstance(value, (dict, list, tuple, set)):
        return len(value) > 0
    if isinstance(value, (str, bytes, bytearray, int, float, bool)) or value is None:
        return False
    if callable(value) and not isinstance(value, type):
        return False
    return hasattr(value, "__dict__")


def _variable(name, value):
    ref = 0
    if _has_children(value):
        _refs.append(value)
        ref = len(_refs)
    return {"name": name, "type": type(value).__name__, "value": _short_repr(value), "ref": ref}


def _children(value):
    if isinstance(value, dict):
        items = [(_short_repr(key), item) for key, item in value.items()]
    elif isinstance(value, (list, tuple)):
        items = [(str(index), item) for index, item in enumerate(value)]
    elif isinstance(value, set):
        items = [(str(index), item) for index, item in enumerate(value)]
    else:
        items = sorted(value.__dict__.items())
    return [_variable(name, item) for name, item in items[:MAX_CHILDREN]]


def _locals(frame):
    if frame.f_code.co_name == "<module>":
        return None
    try:
        items = frame.f_locals.items()
    except AttributeError:
        return None
    return [_variable(name, value) for name, value in sorted(items)]


def _globals(frame):
    variables = []
    for name, value in sorted(frame.f_globals.items()):
        if name.startswith("__"):
            continue
        if type(value).__name__ == "module":
            continue
        variables.append(_variable(name, value))
    return variables


def _handle(command):
    global _mode, _step_frame, _resume, _initialised
    name = command.get("cmd")

    if name == "init":
        _initialised = True
        _breakpoints.clear()
        for filename, lines in command.get("breakpoints", {}).items():
            _breakpoints[filename] = set(lines)
        if command.get("stopOnEntry"):
            _mode = "step_in"

    elif name == "setBreakpoints":
        lines = command.get("lines", [])
        if lines:
            _breakpoints[command["file"]] = set(lines)
        else:
            _breakpoints.pop(command["file"], None)

    elif name == "pause":
        _mode = "pause"

    elif name in ("continue", "stepIn", "stepOver", "stepOut"):
        if not _stopped_frames:
            return
        _mode = {"continue": "run", "stepIn": "step_in", "stepOver": "step_over", "stepOut": "step_out"}[name]
        _step_frame = _stopped_frames[0]
        _resume = True

    elif name == "scopes":
        frame = _stopped_frames[command.get("frame", 0)]
        _send({"event": "scopes", "id": command.get("id"), "frame": command.get("frame", 0), "locals": _locals(frame), "globals": _globals(frame)})

    elif name == "expand":
        ref = command.get("ref", 0)
        children = _children(_refs[ref - 1]) if 0 < ref <= len(_refs) else []
        _send({"event": "children", "id": command.get("id"), "ref": ref, "children": children})

    elif name == "eval":
        frame = _stopped_frames[command.get("frame", 0)] if _stopped_frames else None
        scope = frame.f_globals if frame else {}
        local_scope = frame.f_locals if frame and frame.f_code.co_name != "<module>" else scope
        expression = command.get("expr", "")
        try:
            try:
                result = _variable("result", eval(expression, scope, local_scope))
            except SyntaxError:
                exec(expression, scope, local_scope)
                result = _variable("result", None)
            _send({"event": "evaluated", "id": command.get("id"), "result": result})
        except Exception as e:  # noqa: BLE001
            _send({"event": "evaluated", "id": command.get("id"), "error": type(e).__name__ + ": " + str(e)})


def _poll():
    global _rx
    if not cdcaux.any():
        return
    _rx += cdcaux.read()
    while b"\n" in _rx:
        line, _rx = _rx.split(b"\n", 1)
        if line.strip():
            try:
                _handle(json.loads(line))
            except Exception as e:  # noqa: BLE001
                _send({"event": "error", "message": type(e).__name__ + ": " + str(e)})


def _stop(frame, reason):
    global _resume, _stopped_frames
    _stopped_frames = _stack(frame)
    _refs.clear()
    _resume = False
    _send({
        "event": "stopped",
        "reason": reason,
        "stack": [
            {"file": _frame_file(f), "line": f.f_lineno, "name": f.f_code.co_name, "user": _is_user_file(_frame_file(f))}
            for f in _stopped_frames
        ],
    })
    while not _resume:
        _poll()
        time.sleep_ms(5)
    _stopped_frames = []
    _refs.clear()
    _send({"event": "continued"})


def _should_stop(frame):
    lines = _breakpoints.get(_frame_file(frame))
    if lines and frame.f_lineno in lines:
        return "breakpoint"
    if _mode == "pause":
        return "pause"
    if _mode == "step_in":
        return "step"
    if _mode == "step_over" and frame is _step_frame:
        return "step"
    return None


def _trace_local(frame, event, _arg):
    global _mode
    if event == "line":
        _poll()
        reason = _should_stop(frame)
        if reason:
            _stop(frame, reason)
    elif event == "return":
        if frame is _step_frame and _mode in ("step_over", "step_out"):
            _mode = "step_in"
    return _trace_local


def _trace(frame, event, _arg):
    if event != "call":
        return None
    _poll()
    if not _is_user_file(_frame_file(frame)):
        return None
    if _mode != "run" or _frame_file(frame) in _breakpoints:
        return _trace_local
    return None


def start():
    global _mode, _step_frame, _rx, _initialised
    _mode = "run"
    _step_frame = None
    _rx = b""
    _initialised = False
    _breakpoints.clear()
    cdcaux.claim(True)
    while cdcaux.any():
        cdcaux.read()
    _send({"event": "ready"})
    deadline = time.ticks_add(time.ticks_ms(), INIT_TIMEOUT_MS)
    while not _initialised and time.ticks_diff(deadline, time.ticks_ms()) > 0:
        _poll()
        time.sleep_ms(5)
    sys.settrace(_trace)


def stop():
    sys.settrace(None)
    _send({"event": "terminated"})
    cdcaux.claim(False)
