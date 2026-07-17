# cmake file for Raspberry Pi Pico
set(PICO_BOARD "pimoroni_badger2350")
set(PICO_BOARD_HEADER_DIRS ${CMAKE_CURRENT_LIST_DIR})
set(PICO_PLATFORM "rp2350")
set(PICO_NUM_GPIOS 30)

# Board specific version of the frozen manifest
set(MICROPY_FROZEN_MANIFEST ${MICROPY_BOARD_DIR}/manifest.py)

if(NOT DEFINED MICROPY_HW_ROMFS_BYTES)
    # set(MICROPY_HW_ROMFS_BYTES 1048576)  # 1 * 1024 * 1024
    math(EXPR MICROPY_HW_ROMFS_BYTES "1 * 1024 * 1024")
endif()

if(NOT DEFINED MICROPY_HW_FLASH_STORAGE_BYTES)
    # set(MICROPY_HW_FLASH_STORAGE_BYTES 13631488)  # 16 * 1024 * 1024 - 1MB for ROMFS and 2MB for firmware
    math(EXPR MICROPY_HW_FLASH_STORAGE_BYTES "(14 * 1024 * 1024) - ${MICROPY_HW_ROMFS_BYTES}")
endif()

add_compile_options(-fno-math-errno)   # hardware VSQRT on the M33 FPU (safe: MP math uses isnan/isinf, not errno)

set(MICROPY_C_HEAP_SIZE 4096)

# Enable PSRAM, should pick up CS and size from
# the board header file.
set(MICROPY_HW_ENABLE_PSRAM 1)

# Links micropy_lib_lwip and sets MICROPY_PY_LWIP = 1
# Picked up and expanded upon in mpconfigboard.h
set(MICROPY_PY_LWIP ON)

# Links cyw43-driver and sets:
# MICROPY_PY_NETWORK_CYW43 = 1,
# MICROPY_PY_SOCKET_DEFAULT_TIMEOUT_MS = 30000
set(MICROPY_PY_NETWORK_CYW43 ON)

# Adds mpbthciport.c
# And sets:
# MICROPY_PY_BLUETOOTH = 1,
# MICROPY_PY_BLUETOOTH_USE_SYNC_EVENTS = 1,
# MICROPY_PY_BLUETOOTH_ENABLE_CENTRAL_MODE = 1
set(MICROPY_PY_BLUETOOTH ON)

# Links pico_btstack_hci_transport_cyw43
# And sets:
# MICROPY_BLUETOOTH_BTSTACK = 1,
# MICROPY_BLUETOOTH_BTSTACK_CONFIG_FILE =
set(MICROPY_BLUETOOTH_BTSTACK ON)

# Sets:
# CYW43_ENABLE_BLUETOOTH = 1,
# MICROPY_PY_BLUETOOTH_CYW43 = 1
set(MICROPY_PY_BLUETOOTH_CYW43 ON)

set(PIMORONI_FATFS_DIR ${CMAKE_CURRENT_LIST_DIR}/../firmware)
set(PIMORONI_FATFS_LABEL "BADGER")
set(PIMORONI_ROMFS_DIR ${CMAKE_CURRENT_LIST_DIR}/../romfs)
math(EXPR PIMORONI_LFS_RESERVED "1 * 1024 * 1024")  # Reserve 1MB for LittleFS
include(${CMAKE_CURRENT_LIST_DIR}/filesystem.cmake)
