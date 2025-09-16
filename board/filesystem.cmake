# Make sure we get our VirtualEnv Python
set(Python_FIND_VIRTUALENV "FIRST")
set(Python_FIND_UNVERSIONED_NAMES "FIRST")
set(Python_FIND_STRATEGY "LOCATION")
find_package (Python COMPONENTS Interpreter Development)

message("dir2uf2/py_decl: Using Python ${Python_EXECUTABLE}")

# Convert supplies paths to absolute, for a quieter life
get_filename_component(PIMORONI_UF2_DIR ${PIMORONI_UF2_DIR} REALPATH)

if (EXISTS "${PIMORONI_TOOLS_DIR}/py_decl/py_decl.py")
    add_custom_target("${MICROPY_TARGET}-verify" ALL
        COMMAND ${Python_EXECUTABLE} "${PIMORONI_TOOLS_DIR}/py_decl/py_decl.py" --to-json --verify "${CMAKE_CURRENT_BINARY_DIR}/${MICROPY_TARGET}.uf2"
        WORKING_DIRECTORY ${CMAKE_CURRENT_BINARY_DIR}
        COMMENT "pydecl: Verifying ${MICROPY_TARGET}.uf2"
        DEPENDS ${MICROPY_TARGET}
    )
endif()

if (EXISTS "${PIMORONI_TOOLS_DIR}/ffsmake/build/ffsmake" AND EXISTS "${PIMORONI_UF2_DIR}")
    MESSAGE("ffsmake: Using root ${PIMORONI_UF2_DIR}.")
    MESSAGE("ffsmake: Outputting filesystem binary: ${CMAKE_BINARY_DIR}/${MICROPY_TARGET}-fatfs.bin")
    add_custom_target("${MICROPY_TARGET}-fatfs.bin" ALL
        COMMAND "${PIMORONI_TOOLS_DIR}/ffsmake/build/ffsmake" --force --directory "${PIMORONI_UF2_DIR}" --output "${CMAKE_BINARY_DIR}/${MICROPY_TARGET}-fatfs.bin"
        WORKING_DIRECTORY ${CMAKE_CURRENT_BINARY_DIR}
        COMMENT "ffsmake: Packing FatFS filesystem to ${MICROPY_TARGET}-fatfs.bin."
        DEPENDS ${MICROPY_TARGET}
        DEPENDS "${MICROPY_TARGET}-verify"
    )
endif()

if (EXISTS "${PIMORONI_TOOLS_DIR}/dir2uf2/dir2uf2" AND EXISTS "${PIMORONI_UF2_DIR}")
    MESSAGE("dir2uf2: Using filesystem binary: ${CMAKE_BINARY_DIR}/${MICROPY_TARGET}-fatfs.bin")
    add_custom_target("${MICROPY_TARGET}-with-filesystem.uf2" ALL
        COMMAND ${Python_EXECUTABLE} "${PIMORONI_TOOLS_DIR}/dir2uf2/dir2uf2" --fs-reserve 262144 --sparse --append-to "${MICROPY_TARGET}.uf2" --filename with-filesystem.uf2 "${CMAKE_BINARY_DIR}/${MICROPY_TARGET}-fatfs.bin"
        WORKING_DIRECTORY ${CMAKE_CURRENT_BINARY_DIR}
        COMMENT "dir2uf2: Appending filesystem to ${MICROPY_TARGET}.uf2."
        DEPENDS ${MICROPY_TARGET}
        DEPENDS "${MICROPY_TARGET}-fatfs.bin"
        DEPENDS "${MICROPY_TARGET}-verify"
    )
endif()