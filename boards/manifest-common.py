# from include("$(PORT_DIR)/boards/manifest.py")
freeze("$(PORT_DIR)/modules", "rp2.py")
include("$(MPY_DIR)/extmod/asyncio")

# Handy for dealing with APIs
require("datetime")

freeze("../modules/python/")
freeze("../modules/common/")