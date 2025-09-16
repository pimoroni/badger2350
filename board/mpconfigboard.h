// Board and hardware specific configuration
#define MICROPY_HW_BOARD_NAME                   "Badger 2350"

#define MICROPY_HW_FLASH_STORAGE_BYTES          (PICO_FLASH_SIZE_BYTES - (2 * 1024 * 1024))

// Set up networking.
#define MICROPY_PY_NETWORK_HOSTNAME_DEFAULT     "Badger2350"

// Enable WiFi & PPP
#define MICROPY_PY_NETWORK                      (1)

// CYW43 driver configuration.
#define CYW43_USE_SPI                           (1)
#define CYW43_LWIP                              (1)
#define CYW43_GPIO                              (0)
#define CYW43_SPI_PIO                           (1)

#define MICROPY_HW_PIN_EXT_COUNT    CYW43_WL_GPIO_COUNT

int mp_hal_is_pin_reserved(int n);
#define MICROPY_HW_PIN_RESERVED(i) mp_hal_is_pin_reserved(i)

#define MICROPY_PY_THREAD                       (0)

#define MICROPY_HW_USB_MSC                      (1)
#define MICROPY_HW_USB_DESC_STR_MAX             (40)
#define MICROPY_HW_USB_MANUFACTURER_STRING      "Pimoroni"
#define MICROPY_HW_USB_PRODUCT_FS_STRING        MICROPY_HW_BOARD_NAME " MicroPython"