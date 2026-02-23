from badgeware import clear_running

# Set the running app back to menu, or we'll reset into msc on exit
clear_running()

import _msc.py   # noqa F401
