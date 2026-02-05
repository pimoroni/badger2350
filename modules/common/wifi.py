
import network
import secrets
from badgeware import fatal_error


_timeout_ticks = None
_timeout = 0
_retries = 0
wlan = None


_status_text = {
  0: "Idle",
  1: "Connecting to {ssid}",
  2: "Connected",
  -3: "Incorrect password.",
  -2: "Access point {ssid} not found.",
  -1: "Connection failed.",
  3: "Got IP",
}


def get_status(index):
  return _status_text[index].format(ssid=_ssid, psk=_psk)


def tick():
  global _timeout_ticks, _timeout, _retries, _ssid, _psk

  if wlan is not None and wlan.isconnected():
    return True

  timed_out = _timeout_ticks is not None and badge.ticks > _timeout_ticks
  error = wlan is not None and wlan.status() not in (0, 1, 2, 3)

  if (timed_out or error):
    if _retries:
      _retries -= 1
      _timeout_ticks = badge.ticks + (_timeout * 1000)
      wlan.connect(_ssid, _psk)
      return False

    wlan.active(False)
    fatal_error("WiFi Connection Timed Out" if timed_out else "WiFi Connection Failed", get_status(wlan.status()))
    _timeout_ticks = None

  return False


def connect(ssid=None, psk=None, timeout=60, retries=5):
  global wlan, _timeout_ticks, _timeout, _retries, _ssid, _psk

  if ssid is None and psk is None:
    ssid = secrets.WIFI_SSID
    psk = secrets.WIFI_PASSWORD

    if not ssid:
      fatal_error("Missing Details!", "Put your badge into disk mode (tap RESET twice)\nEdit 'secrets.py' to set WiFi details and your local region")

  if wlan:
    return wlan.isconnected()

  wlan = network.WLAN(network.STA_IF)
  wlan.active(True)
  # Already connected from a previous attempt
  if wlan.isconnected():
    return True
  _ssid = ssid
  _psk = psk
  _retries = retries
  _timeout = timeout
  wlan.connect(ssid, psk)
  _timeout_ticks = badge.ticks + (timeout * 1000)
  return False


def disconnect():
  global wlan
  if wlan:
    wlan.disconnect()
    wlan.active(False)
    wlan = None


def status():
  global wifi
  if wifi is None:
    return 0, get_status(0)  # Idle
  return wlan.status(), get_status(wlan.status())


def is_connected():
  return wlan is not None and wlan.isconnected()


def ipv4():
  return wlan.ipconfig("addr4")[0] if wlan else None


def ipv6():
  return wlan.ipconfig("addr6")[0][0] if wlan else None


def ip():
  return ipv4()


def subnet():
  return wlan.ifconfig()[1] if wlan else None


def gateway():
  return wlan.ifconfig()[2] if wlan else None


def nameserver():
  return wlan.ifconfig()[3] if wlan else None
