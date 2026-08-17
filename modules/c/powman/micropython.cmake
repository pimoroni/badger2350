add_library(usermod_sleep INTERFACE)

target_sources(usermod_sleep INTERFACE
    ${CMAKE_CURRENT_LIST_DIR}/bindings.c
    ${CMAKE_CURRENT_LIST_DIR}/powman.c
    ${CMAKE_CURRENT_LIST_DIR}/rosc.c
)

target_include_directories(usermod_sleep INTERFACE
    ${CMAKE_CURRENT_LIST_DIR}
    ${PICOVECTOR_DIR}   # picovector_working_buffer.h — the shared scratch pool reused as the parser arena
)

target_link_libraries(usermod_sleep INTERFACE hardware_powman hardware_gpio hardware_psram)

target_link_libraries(usermod INTERFACE usermod_sleep)

set_source_files_properties(
    ${CMAKE_CURRENT_LIST_DIR}/bindings.c
    PROPERTIES COMPILE_FLAGS
    "-Wno-discarded-qualifiers"
)
