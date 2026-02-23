#pragma once

#include <initializer_list>

#include "pico/stdlib.h"
#include "hardware/spi.h"
#include "hardware/gpio.h"

#include "common/pimoroni_common.hpp"
#include "common/pimoroni_bus.hpp"

namespace pimoroni {

  class SSD1680 {
    enum RAM_FLAGS {
      X_START    = 0x00,
      X_END      = 0x15, // 0x15 = (176 / 8) - 1
      Y_START_H  = 0x01, // 0x01 = (264 >> 8)
      Y_START_L  = 0x07, // 0x07 = (264 & 0xff) - 1
      Y_END_H    = 0x00,
      Y_END_L    = 0x00
    };

    //--------------------------------------------------
    // Variables
    //--------------------------------------------------
  private:
    spi_inst_t *spi = spi0;

    // interface pins with our standard defaults where appropriate
    const uint CS     = 17;
    const uint DC     = 20;
    const uint SCK    = 18;
    const uint MOSI   = 19;
    const uint BUSY   = 16;
    const uint RESET  = 21;

    uint8_t lut_repeat_count = 1; // Default to 1 for a ghost-free but slightly slower refresh
    bool inverted = true; // Makes 0 black and 1 white, as is foretold.
    bool blocking = true;

  public:
    SSD1680() {
      // configure spi interface and pins
      spi_init(spi, 12'000'000);

      gpio_set_function(DC, GPIO_FUNC_SIO);
      gpio_set_dir(DC, GPIO_OUT);

      gpio_set_function(CS, GPIO_FUNC_SIO);
      gpio_set_dir(CS, GPIO_OUT);
      gpio_put(CS, 1);

      gpio_set_function(RESET, GPIO_FUNC_SIO);
      gpio_set_dir(RESET, GPIO_OUT);
      gpio_put(RESET, 1);

      gpio_set_function(BUSY, GPIO_FUNC_SIO);
      gpio_set_dir(BUSY, GPIO_IN);

      gpio_set_function(SCK,  GPIO_FUNC_SPI);
      gpio_set_function(MOSI, GPIO_FUNC_SPI);

      setup();

      write_luts();
    }

    ~SSD1680() {
      // todo: teardown
    }

    //--------------------------------------------------
    // Methods
    //--------------------------------------------------
  public:
    void update();
    uint32_t *get_framebuffer();

    void busy_wait();
    void reset();

    bool is_busy();
    bool set_update_speed(int update_speed);

    void write_luts();
    void set_blocking(bool blocking);

    void command(uint8_t reg, size_t len, const uint8_t *data);

  private:
    void setup();

    void read(uint8_t reg, size_t len, uint8_t *data);
    void command(uint8_t reg, std::initializer_list<uint8_t> values);
    void command(uint8_t reg) {command(reg, 0, nullptr);};
    void data(size_t len, const uint8_t *data);
    void data(std::initializer_list<uint8_t> values);
  };

}
