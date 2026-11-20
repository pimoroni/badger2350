ASSERT((((end & 0xfff) + 1112) / 4096 + 1) * 4096 - (end & 0xfff) <= __micropy_c_heap_size__, "C heap too small for the exception pool at this __bss_end__ page offset, raise MICROPY_C_HEAP_SIZE")
