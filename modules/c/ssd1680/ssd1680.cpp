#include "ssd1680.hpp"

#include <cstdlib>
#include <math.h>
#include <string.h>

#ifdef MICROPY_BUILD_TYPE
extern "C" {
#include "py/runtime.h"
}
#endif

namespace pimoroni {
  constexpr int WIDTH = 264;
  constexpr int HEIGHT = 176;

  uint32_t __attribute__((section(".uninitialized_data"))) __attribute__((aligned (4))) framebuffer[WIDTH * HEIGHT];

  uint8_t __attribute__((section(".uninitialized_data"))) backbuffer[(WIDTH * HEIGHT) / 8];

  enum reg {
    DOC      = 0x01,  // Set Gate Driver Output
    GDVC     = 0x03,  // Gate level voltage control
    SDVC     = 0x04,  // source driving voltage control
    BTST     = 0x0C,  // booster soft start
    DSM      = 0x10,  // deep sleep mode
    DEM      = 0x11,   // data entry mode
    SWR      = 0x12,  // SW RESET
    ADUS     = 0x20,  // activate display update
    DUC1     = 0x21,  // display update control 1
    DUC2     = 0x22,  // display update control 2
    WRAM_BW  = 0x24,  // Write RAM (Black White)
    WRAM_R   = 0x26,  // Write RAM (Red) or gray in our case.
    READ_RAM = 0x27,
    WVCOM    = 0x2C,  // write VCOM reg
    WLR      = 0x32,  // write LUT register
    BWCTRL   = 0x3C,  // border waveform control
    EOPT     = 0x3F,  // option for LUT end
    READ_RAM_OPT = 0x41, // read ram option
    SRX      = 0x44,  // set RAM x start/end pos
    SRY      = 0x45,  // set RAM y start/end pos
    SRXC     = 0x4E,  // set RAM x counter
    SRYC     = 0x4F,  // set RAM y counter
  };

  void SSD1680::set_blocking(bool blocking) {
    this->blocking = blocking;
  }

  bool SSD1680::is_busy() {
    if(BUSY == PIN_UNUSED) return false;
    return gpio_get(BUSY);
  }

  void SSD1680::busy_wait() {
    while(is_busy()) {
#ifdef MICROPY_BUILD_TYPE
      mp_handle_pending(true);
#endif
      tight_loop_contents();
    }
  }

  uint32_t *SSD1680::get_framebuffer() {
    return framebuffer;
  }

  void SSD1680::reset() {
    if(RESET == PIN_UNUSED) return;
    gpio_put(RESET, 0); sleep_ms(10);
    gpio_put(RESET, 1); sleep_ms(10);
    busy_wait();
  }

  bool SSD1680::set_update_speed(int update_speed) {
    // 0 == slow (lut_repeat_count of 3), 3 == fast (lut_repeat_count of 0)
    this->lut_repeat_count = (uint8_t)3 - (uint8_t)(update_speed & 3);
    return true;
  }

  void SSD1680::write_luts() {
    command(WLR, {
//    Group:
//    0     1     2     3     4     5     6     7     8     9     10    11
      0x40, 0x68, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, // VS L0
      0xA0, 0x65, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, // VS L1
      0xA8, 0x65, 0x40, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, // VS L2
      0xAA, 0x65, 0x50, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, // VS L3
      0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, // VS L4
    });
//    Phase:
//        L0    L1    L2    L3    L4    SR?             Repeat
    data({0x02, 0x00, 0x00, 0x05, 0x0A, 0x00}); data(1, &this->lut_repeat_count); // Group0
    data({0x19, 0x19, 0x00, 0x02, 0x00, 0x00}); data(1, &this->lut_repeat_count); // Group1
    data({0x05, 0x0A, 0x00, 0x00, 0x00, 0x00}); data(1, &this->lut_repeat_count); // Group2

    // Remaining unused LUTs and config values
    data({
      0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, // Group3
      0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, // Group4
      0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, // Group5
      0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, // Group6
      0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, // Group7
      0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, // Group8
      0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, // Group9
      0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, // Group10
      0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, // Group11
//    Config:
      0x44, 0x42, 0x22, 0x22, 0x23, 0x32, 0x00, 0x00, 0x00 // FR, XON
    });

    command(EOPT, {0x22});
    command(GDVC, {0x17});
    command(SDVC, {0x41, 0xAE, 0x32});
    command(WVCOM, {0x28});

    busy_wait();

  }

  void SSD1680::setup() {
    reset();

    command(SWR);
    busy_wait();

    command(DOC, {Y_START_L, Y_START_H, 0});
    //command(0x3A, {27}); // Dummy line period?
    //command(0x3B, {55}); // Gateline?

    // 0b100 == Swap X / Y
    // 0b010 == Y invert (ie: counts up)
    // 0b001 == X invert (ie counts up)
    command(DEM, {0b001}); // x+ y-
    command(SRX, {X_START, X_END});
    command(SRY, {Y_START_L, Y_START_H, Y_END_L, Y_END_H});
    //command(BWCTRL, {0x00});

    busy_wait();

  }

  void SSD1680::read(uint8_t reg, size_t len, uint8_t *data) {
    gpio_put(CS, 0);

    gpio_put(DC, 0); // command mode
    spi_write_blocking(spi, &reg, 1);

    if(len > 0) {
      gpio_put(DC, 1); // data mode
      gpio_set_function(SCK,  GPIO_FUNC_SIO);
      gpio_set_dir(SCK, GPIO_OUT);
      gpio_set_function(MOSI, GPIO_FUNC_SIO);
      gpio_set_dir(MOSI, GPIO_IN);
      for(auto i = 0u; i < len; i++) {
        int byte = i / 8;
        int bit = i % 8;
        gpio_put(SCK, true);
        bool value = gpio_get(MOSI);
        data[byte] |= value << (7-bit);
        gpio_put(SCK, false);
      }

      gpio_set_function(SCK,  GPIO_FUNC_SPI);
      gpio_set_function(MOSI, GPIO_FUNC_SPI);
    }

    gpio_put(CS, 1);
  }

  void SSD1680::command(uint8_t reg, size_t len, const uint8_t *data) {
    gpio_put(CS, 0);

    gpio_put(DC, 0); // command mode
    spi_write_blocking(spi, &reg, 1);

    if(len > 0) {
      gpio_put(DC, 1); // data mode
      spi_write_blocking(spi, (const uint8_t*)data, len);

    }

    gpio_put(CS, 1);

  }

  void SSD1680::data(size_t len, const uint8_t *data) {
    gpio_put(CS, 0);
    gpio_put(DC, 1); // data mode
    spi_write_blocking(spi, (const uint8_t*)data, len);
    gpio_put(CS, 1);
  }

  void SSD1680::data(std::initializer_list<uint8_t> values) {
    data(values.size(), (uint8_t *)values.begin());
  }

  void SSD1680::command(uint8_t reg, std::initializer_list<uint8_t> values) {
    command(reg, values.size(), (uint8_t *)values.begin());
  }

  void SSD1680::update() {
    // Wait for any previous update to finish
    busy_wait();

    // Write the LUTs (~200us)
    write_luts();

    command(SRXC, {X_START});
    command(SRYC, {Y_START_L, Y_START_H});

    command(WRAM_R);
    memset(backbuffer, 0, sizeof(backbuffer));
    for(auto y = 0; y < HEIGHT; y++) {
      for(auto x = 0; x < WIDTH; x++) {
        uint bo_d = 7 - (y & 0b111);
        uint32_t fb_src = framebuffer[x + y * WIDTH];
        uint8_t src = ((fb_src & 0x00ff0000) >> 16) | ((fb_src & 0x0000ff00) >> 8) | ((fb_src & 0x000000ff));
        src = ~(src >> 7) & 0b1;
        backbuffer[(y + x * HEIGHT) / 8] |= (src << bo_d);
      }
    }
    data(sizeof(backbuffer), (const uint8_t*)backbuffer);

    command(SRXC, {X_START});
    command(SRYC, {Y_START_L, Y_START_H});

    command(WRAM_BW);
    memset(backbuffer, 0, sizeof(backbuffer));
    for(auto y = 0; y < HEIGHT; y++) {
      for(auto x = 0; x < WIDTH; x++) {
        uint bo_d = 7 - (y & 0b111);
        uint32_t fb_src = framebuffer[x + y * WIDTH];
        uint8_t src = ((fb_src & 0x00ff0000) >> 16) | ((fb_src & 0x0000ff00) >> 8) | ((fb_src & 0x000000ff));
        src = ~(src >> 6) & 0b1;
        backbuffer[(y + x * HEIGHT) / 8] |= (src << bo_d);
      }
    }
    data(sizeof(backbuffer), (const uint8_t*)backbuffer);

    command(BTST);
    command(DUC2, {0xC7});

    busy_wait();

    command(ADUS);

    if(blocking) {
      busy_wait();
    }

  }
}
