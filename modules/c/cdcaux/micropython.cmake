add_library(usermod_cdcaux INTERFACE)

target_sources(usermod_cdcaux INTERFACE
    ${CMAKE_CURRENT_LIST_DIR}/cdcaux.c
)

target_include_directories(usermod_cdcaux INTERFACE
    ${CMAKE_CURRENT_LIST_DIR}
)

target_link_libraries(usermod INTERFACE usermod_cdcaux)
