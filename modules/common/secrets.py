from badgeware import fatal_error


WIFI_SSID = ""
WIFI_PASSWORD = ""
REGION = "eu"
TIMEZONE = 0
LAT = ""
LON = ""

try:
    _from_file = __import__("/secrets").__dict__
except ImportError:
    _from_file = {}

for _key, _value in _from_file.items():
    if not _key.startswith("__"):
        globals()[_key] = _value

del _from_file


def require(*keys):
    import secrets
    keys = [key for key in keys if getattr(secrets, key, None) in (None, "")]
    if keys:
        required = ", ".join(keys)
        fatal_error("Missing Secrets!", f"Connect to the Badgeware IDE and open Config to set {required}.")
