if(NOT DEFINED PIMORONI_PICO_PATH)
set(PIMORONI_PICO_PATH ${CMAKE_CURRENT_LIST_DIR}/../pimoroni-pico)
endif()
include(${PIMORONI_PICO_PATH}/pimoroni_pico_import.cmake)

include_directories(${CMAKE_CURRENT_LIST_DIR}/../../)
include_directories(${PIMORONI_PICO_PATH}/micropython)

# Drivers, etc
list(APPEND CMAKE_MODULE_PATH "${PIMORONI_PICO_PATH}")
# modules_py/modules_py
list(APPEND CMAKE_MODULE_PATH "${PIMORONI_PICO_PATH}/micropython")
# All regular modules
list(APPEND CMAKE_MODULE_PATH "${PIMORONI_PICO_PATH}/micropython/modules")

# Allows us to find downstream /modules/c/*/
list(APPEND CMAKE_MODULE_PATH "${CMAKE_CURRENT_LIST_DIR}/..")

set(CMAKE_C_STANDARD 17)
set(CMAKE_CXX_STANDARD 17)

# PicoVector and supporting libs
find_package(PICOVECTOR CONFIG REQUIRED)

# Build picovector for Tufty 2350
target_compile_definitions(usermod_picovector INTERFACE BADGER=1)

# Essential
include(pimoroni_i2c/micropython)

# Badger display driver
include(modules/c/ssd1680/micropython)

# QR Code Module
include(qrcode/micropython/micropython)

# Sensors & Breakouts
include(micropython-common-breakouts)

# Driver for RTC
include(pcf85063a/micropython)

# Utility
include(adcfft/micropython)

# Sleep / Wake Reason
include(modules/c/powman/micropython)
target_compile_definitions(usermod_sleep INTERFACE BADGER=1)

# C++ Magic Memory
include(cppmem/micropython)

# Disable build-busting C++ exceptions
include(micropython-disable-exceptions)

# Must call `enable_ulab()` to enable
include(micropython-common-ulab)
enable_ulab()
