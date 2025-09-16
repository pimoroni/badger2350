import machine

# Pull all of the machine.Pin.board.LABEL definitions into the local scope
# Note The firmware (via powman startup) will guarantee these are configured.
locals().update((k,v) for (k,v) in machine.Pin.board.__dict__.items() if not k.startswith("_"))
