if (NOT DEFINED JPEGDEC_ONCE)
    set (JPEGDEC_ONCE TRUE)

    add_library(jpegdec
        ${CMAKE_CURRENT_LIST_DIR}/JPEGDEC.cpp
    )

    set_source_files_properties(${CMAKE_CURRENT_LIST_DIR}/JPEGDEC.cpp PROPERTIES COMPILE_FLAGS "-Wno-error=unused-function")

    target_include_directories(jpegdec INTERFACE ${CMAKE_CURRENT_LIST_DIR})
endif() 