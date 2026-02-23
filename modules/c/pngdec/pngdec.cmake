if (NOT DEFINED PNGDEC_ONCE)
    set (PNGDEC_ONCE TRUE)

    list(APPEND SOURCES
      ${CMAKE_CURRENT_LIST_DIR}/PNGdec.cpp
      ${CMAKE_CURRENT_LIST_DIR}/adler32.c
      ${CMAKE_CURRENT_LIST_DIR}/crc32.c
      ${CMAKE_CURRENT_LIST_DIR}/infback.c
      ${CMAKE_CURRENT_LIST_DIR}/inffast.c
      ${CMAKE_CURRENT_LIST_DIR}/inflate.c
      ${CMAKE_CURRENT_LIST_DIR}/inftrees.c
      ${CMAKE_CURRENT_LIST_DIR}/zutil.c
    )

    add_library(pngdec
      ${SOURCES}
    )

    set_source_files_properties(${SOURCES} PROPERTIES COMPILE_OPTIONS "-Wno-deprecated-non-prototype;-Wno-error=unused-function")

    target_include_directories(pngdec INTERFACE ${CMAKE_CURRENT_LIST_DIR})

    target_link_libraries(pngdec)

endif() 