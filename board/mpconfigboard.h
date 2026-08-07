// Board and hardware specific configuration
#define MICROPY_HW_BOARD_NAME                   "Pimoroni Badger 2350"

// Replaced in CMake
// #define MICROPY_HW_ROMFS_BYTES                  (1 * 1024 * 1024)
// #define MICROPY_HW_FLASH_STORAGE_BYTES          (PICO_FLASH_SIZE_BYTES - (2 * 1024 * 1024) - MICROPY_HW_ROMFS_BYTES)

#define MICROPY_OBJ_REPR (MICROPY_OBJ_REPR_C)

#define MICROPY_GC_NO_SCAN   (1)   // big PSRAM GC win; NO_CLEAR benefit comes with it

// Default is 4 * MP_BYTES_PER_OBJ_WORD, ie. 16 bytes here. Only single-block
// allocations advance the collector's free-block hint (py/gc.c, n_free == 1), so on a
// heap this size every multi-block allocation rescans the allocation table: measured at
// ~31k table bytes per 2-block allocation, and ~10x the cost of a 1-block one. 32 bytes
// brings rect, 3-element tuples and the 6-float mat3 into a single block. It costs
// internal fragmentation, which 8MB of PSRAM can afford, and shortens the consecutive
// run search for large allocations. Unix port: collect pause down a fifth to a quarter.
#define MICROPY_BYTES_PER_GC_BLOCK (32)

#define MICROPY_HW_VM_IN_RAM (1)   // OPTIONAL: ~+20% interp, costs ~6 KB SRAM (.data)
                                   //  - keep only if the build still links.

// Set up networking.
#define MICROPY_PY_NETWORK_HOSTNAME_DEFAULT     "Badger2350"

// Enable WiFi & PPP
#define MICROPY_PY_NETWORK                      (1)

// CYW43 driver configuration.
#define CYW43_USE_SPI                           (1)
#define CYW43_LWIP                              (1)
#define CYW43_GPIO                              (1)
#define CYW43_SPI_PIO                           (1)

#define MICROPY_HW_PIN_EXT_COUNT    CYW43_WL_GPIO_COUNT

int mp_hal_is_pin_reserved(int n);
#define MICROPY_HW_PIN_RESERVED(i) mp_hal_is_pin_reserved(i)

// Skip default pins
#define MICROPY_HW_SPI_NO_DEFAULT_PINS          (1)
#define MICROPY_HW_UART_NO_DEFAULT_PINS         (1)

// Don't use SRAM for MicroPython heap
#define MICROPY_GC_SPLIT_HEAP                   (0)

#define MICROPY_PY_THREAD                       (0)

// Configure USB
#define MICROPY_HW_USB_VID                      (0x2e8a)
#define MICROPY_HW_USB_PID                      (0x1100)

#define MICROPY_HW_USB_MSC                      (1)
#define MICROPY_HW_USB_DESC_STR_MAX             (40)
#define MICROPY_HW_USB_MANUFACTURER_STRING      "Pimoroni"
#define MICROPY_HW_USB_PRODUCT_FS_STRING        MICROPY_HW_BOARD_NAME " MicroPython"