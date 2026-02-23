add_library(usermod_picovector INTERFACE)

find_package(PNGDEC CONFIG REQUIRED)
find_package(JPEGDEC CONFIG REQUIRED)

list(APPEND SOURCES
  ${CMAKE_CURRENT_LIST_DIR}/micropython/picovector_bindings.c
  ${CMAKE_CURRENT_LIST_DIR}/micropython/picovector.cpp
  ${CMAKE_CURRENT_LIST_DIR}/picovector.cpp
  ${CMAKE_CURRENT_LIST_DIR}/shape.cpp
  ${CMAKE_CURRENT_LIST_DIR}/font.cpp
  ${CMAKE_CURRENT_LIST_DIR}/pixel_font.cpp
  ${CMAKE_CURRENT_LIST_DIR}/image.cpp
  ${CMAKE_CURRENT_LIST_DIR}/brush.cpp
  ${CMAKE_CURRENT_LIST_DIR}/color.cpp
  ${CMAKE_CURRENT_LIST_DIR}/primitive.cpp
  ${CMAKE_CURRENT_LIST_DIR}/algorithms/geometry.cpp
  ${CMAKE_CURRENT_LIST_DIR}/algorithms/dda.cpp
  ${CMAKE_CURRENT_LIST_DIR}/brushes/pattern.cpp
  ${CMAKE_CURRENT_LIST_DIR}/brushes/color.cpp
  ${CMAKE_CURRENT_LIST_DIR}/brushes/image.cpp
  ${CMAKE_CURRENT_LIST_DIR}/filters/blur.cpp
  ${CMAKE_CURRENT_LIST_DIR}/filters/dither.cpp
  ${CMAKE_CURRENT_LIST_DIR}/filters/monochrome.cpp
  ${CMAKE_CURRENT_LIST_DIR}/filters/onebit.cpp
  ${CMAKE_CURRENT_LIST_DIR}/micropython/brush.cpp
  ${CMAKE_CURRENT_LIST_DIR}/micropython/color.cpp
  ${CMAKE_CURRENT_LIST_DIR}/micropython/font.cpp
  ${CMAKE_CURRENT_LIST_DIR}/micropython/image_jpeg.cpp
  ${CMAKE_CURRENT_LIST_DIR}/micropython/image_png.cpp
  ${CMAKE_CURRENT_LIST_DIR}/micropython/image.cpp
  ${CMAKE_CURRENT_LIST_DIR}/micropython/input.cpp
  ${CMAKE_CURRENT_LIST_DIR}/micropython/mat3.cpp
  ${CMAKE_CURRENT_LIST_DIR}/micropython/pixel_font.cpp
  ${CMAKE_CURRENT_LIST_DIR}/micropython/shape.cpp
  ${CMAKE_CURRENT_LIST_DIR}/micropython/rect.cpp
  ${CMAKE_CURRENT_LIST_DIR}/micropython/vec2.cpp
  ${CMAKE_CURRENT_LIST_DIR}/micropython/algorithm.cpp
)

target_sources(usermod_picovector INTERFACE
  ${SOURCES}
)

target_include_directories(usermod_picovector INTERFACE
  ${CMAKE_CURRENT_LIST_DIR}
)

target_link_libraries(usermod INTERFACE usermod_picovector pngdec jpegdec)

set_source_files_properties(
  ${SOURCES}
  PROPERTIES COMPILE_FLAGS
  "-Wno-unused-variable"
)

if(DEFINED PICO_BOARD)
  set_source_files_properties(
    ${SOURCES}
    PROPERTIES COMPILE_OPTIONS
    "-O2;-fgcse-after-reload;-floop-interchange;-fpeel-loops;-fpredictive-commoning;-fsplit-paths;-ftree-loop-distribute-patterns;-ftree-loop-distribution;-ftree-vectorize;-ftree-partial-pre;-funswitch-loops"
  )
endif()