from badgeware import fatal_error


try:
    _secrets = __import__("/secrets")
except ImportError:
    _secrets = __import__("/system/secrets")

# Copy contents of secrets to module scope
for k, v in _secrets.__dict__.items():
    if not k.startswith("__"):
        locals()[k] = v

del _secrets, k, v


def require(*keys):
    import secrets
    keys = [key for key in keys if getattr(secrets, key, None) in (None, "")]
    if keys:
        required = ", ".join(keys)
        fatal_error("Missing Secrets!", f"Put your badge into disk mode (tap RESET twice)\nEdit 'secrets.py' and set {required}")
