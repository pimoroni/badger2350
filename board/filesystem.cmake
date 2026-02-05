# Make sure we get our VirtualEnv Python
set(Python_FIND_VIRTUALENV "FIRST")
set(Python_FIND_UNVERSIONED_NAMES "FIRST")
set(Python_FIND_STRATEGY "LOCATION")
find_package (Python COMPONENTS Interpreter Development)

message("dir2uf2/py_decl: Using Python ${Python_EXECUTABLE}")

# Convert supplies paths to absolute, for a quieter life
get_filename_component(PIMORONI_ROMFS_DIR ${PIMORONI_ROMFS_DIR} REALPATH)
get_filename_component(PIMORONI_FATFS_DIR ${PIMORONI_FATFS_DIR} REALPATH)

if (EXISTS "${PIMORONI_TOOLS_DIR}/py_decl/py_decl.py")
    add_custom_target("${MICROPY_TARGET}-verify" ALL
        COMMAND ${Python_EXECUTABLE} "${PIMORONI_TOOLS_DIR}/py_decl/py_decl.py" --to-json --verify "${CMAKE_CURRENT_BINARY_DIR}/${MICROPY_TARGET}.uf2"
        WORKING_DIRECTORY ${CMAKE_CURRENT_BINARY_DIR}
        COMMENT "pydecl: Verifying ${MICROPY_TARGET}.uf2"
        DEPENDS ${MICROPY_TARGET}
    )
endif()

# 4100 sectors (16MB) total
# 256 sectors (1MB) allocated for LFS filesystem
# 512 sectors (2MB) allocated for MicroPython
# 256 sectors (1MB) allocated for ROMFS
# 3076 sectors (~12MB) for user filesystem

if (EXISTS "${PIMORONI_TOOLS_DIR}/ffsmake/build/ffsmake" AND EXISTS "${PIMORONI_FATFS_DIR}")
    MESSAGE("ffsmake: Using root ${PIMORONI_FATFS_DIR}.")
    MESSAGE("ffsmake: Outputting filesystem binary: ${CMAKE_BINARY_DIR}/${MICROPY_TARGET}-fatfs.bin")
    add_custom_target("${MICROPY_TARGET}-fatfs.bin" ALL
        COMMAND "${PIMORONI_TOOLS_DIR}/ffsmake/build/ffsmake" --label="${PIMORONI_FATFS_LABEL}" --sector-count=3076 --force --directory "${PIMORONI_FATFS_DIR}" --output "${CMAKE_BINARY_DIR}/${MICROPY_TARGET}-fatfs.bin"
        WORKING_DIRECTORY ${CMAKE_CURRENT_BINARY_DIR}
        COMMENT "ffsmake: Packing FatFS filesystem to ${MICROPY_TARGET}-fatfs.bin."
        DEPENDS ${MICROPY_TARGET}
        DEPENDS "${MICROPY_TARGET}-verify"
    )
endif()

if (EXISTS "${MICROPY_DIR}/tools/mpremote/mpremote.py" AND EXISTS "${PIMORONI_ROMFS_DIR}")
    MESSAGE("mpremote romfs build: Using root ${PIMORONI_ROMFS_DIR}.")
    MESSAGE("mpremote romfs build: Outputting filesystem binary: ${CMAKE_BINARY_DIR}/${MICROPY_TARGET}-romfs.bin")
    add_custom_target("${MICROPY_TARGET}-romfs.bin" ALL
        COMMAND ${Python_EXECUTABLE} "${MICROPY_DIR}/tools/mpremote/mpremote.py" romfs --output "${CMAKE_BINARY_DIR}/${MICROPY_TARGET}-romfs.bin" build "${PIMORONI_ROMFS_DIR}"
        WORKING_DIRECTORY ${CMAKE_CURRENT_BINARY_DIR}
        COMMENT "mpremote romfs build: Packing ROMFS filesystem to ${MICROPY_TARGET}-romfs.bin."
        DEPENDS ${MICROPY_TARGET}
        DEPENDS "${MICROPY_TARGET}-verify"
    )
endif()

if (EXISTS "${PIMORONI_TOOLS_DIR}/dir2uf2/dir2uf2" AND EXISTS "${PIMORONI_FATFS_DIR}")
    MESSAGE("dir2uf2: Using ROMFS binary: ${CMAKE_BINARY_DIR}/${MICROPY_TARGET}-romfs.bin")
    add_custom_target("${MICROPY_TARGET}-romfs.uf2" ALL
        COMMAND ${Python_EXECUTABLE} "${PIMORONI_TOOLS_DIR}/dir2uf2/dir2uf2" --fs-blockdev ROMFS --sparse --append-to "${MICROPY_TARGET}.uf2" --filename romfs.uf2 "${CMAKE_BINARY_DIR}/${MICROPY_TARGET}-romfs.bin"
        WORKING_DIRECTORY ${CMAKE_CURRENT_BINARY_DIR}
        COMMENT "dir2uf2: Appending ROMFS to ${MICROPY_TARGET}.uf2."
        DEPENDS ${MICROPY_TARGET}
        DEPENDS "${MICROPY_TARGET}-romfs.bin"
        DEPENDS "${MICROPY_TARGET}.uf2"
        DEPENDS "${MICROPY_TARGET}-verify"
    )
endif()

if (EXISTS "${PIMORONI_TOOLS_DIR}/dir2uf2/dir2uf2" AND EXISTS "${PIMORONI_FATFS_DIR}")
    MESSAGE("dir2uf2: Using filesystem binary: ${CMAKE_BINARY_DIR}/${MICROPY_TARGET}-fatfs.bin")
    add_custom_target("${MICROPY_TARGET}-with-filesystem.uf2" ALL
        COMMAND ${Python_EXECUTABLE} "${PIMORONI_TOOLS_DIR}/dir2uf2/dir2uf2" --fs-reserve 1048576 --fs-blockdev MicroPython --sparse --append-to "${MICROPY_TARGET}-romfs.uf2" --filename with-filesystem.uf2 "${CMAKE_BINARY_DIR}/${MICROPY_TARGET}-fatfs.bin"
        WORKING_DIRECTORY ${CMAKE_CURRENT_BINARY_DIR}
        COMMENT "dir2uf2: Appending filesystem to ${MICROPY_TARGET}.uf2."
        DEPENDS "${MICROPY_TARGET}-romfs.uf2"
        DEPENDS "${MICROPY_TARGET}-fatfs.bin"
        DEPENDS "${MICROPY_TARGET}-verify"
    )
endif()