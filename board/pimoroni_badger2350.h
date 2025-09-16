/*
 * Copyright (c) 2024 Raspberry Pi (Trading) Ltd.
 *
 * SPDX-License-Identifier: BSD-3-Clause
 */

// -----------------------------------------------------
// NOTE: THIS HEADER IS ALSO INCLUDED BY ASSEMBLER SO
//       SHOULD ONLY CONSIST OF PREPROCESSOR DIRECTIVES
// -----------------------------------------------------

// This header may be included by other board headers as "boards/pico2_w.h"

// pico_cmake_set PICO_PLATFORM=rp2350
// pico_cmake_set PICO_CYW43_SUPPORTED = 1

#ifndef _BOARDS_PICO2_W_H
#define _BOARDS_PICO2_W_H

// Board config
// RTC = PCF85063e
#define BW_RTC_I2C       i2c0
#define BW_RTC_ADDR      (0x51)
#define BW_RTC_I2C_SDA   (4)
#define BW_RTC_I2C_SCL   (5)

// Rear white LEDs
#define BW_LED_0         (0)
#define BW_LED_1         (1)
#define BW_LED_2         (3)
#define BW_LED_3         (4)

// User inputs
#define BW_SWITCH_A      (7)
#define BW_SWITCH_B      (8)
#define BW_SWITCH_C      (9)
#define BW_SWITCH_UP     (10)
#define BW_SWITCH_DOWN   (6)

// This is wired to the RESET (Disk / Sleep / Reset / Power On)
// button and used to determine long press status
#define BW_RESET_SW      (14) // No pull, active high?

#define BW_CHARGE_STAT   (12)

// I2C power for talking to RTC
#define BW_SW_POWER_EN   (27)

// Interrupt channels for GPIO wakeup
#define BW_VBUS_DETECT   (11) // No pull, active high?
#define BW_RTC_ALARM     (13) // Pull up, active low
#define BW_SWITCH_HOME   (22) // AKA boot
#define BW_SWITCH_INT    (15) // Pull up, active low
#define BW_SWITCH_MASK   ((1 << BW_SWITCH_A) | (1 << BW_SWITCH_B) | (1 << BW_SWITCH_C) | (1 << BW_SWITCH_UP) | (1 << BW_SWITCH_DOWN))

// For board detection
#define RASPBERRYPI_PICO2_W

// --- RP2350 VARIANT ---
#define PICO_RP2350A 1

// --- UART ---
// no PICO_DEFAULT_UART
// no PICO_DEFAULT_UART_TX_PIN
// no PICO_DEFAULT_UART_RX_PIN

// --- LED ---
// no PICO_DEFAULT_LED_PIN - LED is on Wireless chip
// no PICO_DEFAULT_WS2812_PIN

// --- I2C ---
#ifndef PICO_DEFAULT_I2C
#define PICO_DEFAULT_I2C 0
#endif
#ifndef PICO_DEFAULT_I2C_SDA_PIN
#define PICO_DEFAULT_I2C_SDA_PIN BW_RTC_I2C_SDA
#endif
#ifndef PICO_DEFAULT_I2C_SCL_PIN
#define PICO_DEFAULT_I2C_SCL_PIN BW_RTC_I2C_SCL
#endif

// --- SPI ---
#ifndef PICO_DEFAULT_SPI
#define PICO_DEFAULT_SPI 0
#endif
#ifndef PICO_DEFAULT_SPI_SCK_PIN
#define PICO_DEFAULT_SPI_SCK_PIN 18
#endif
#ifndef PICO_DEFAULT_SPI_TX_PIN
#define PICO_DEFAULT_SPI_TX_PIN 19
#endif
#ifndef PICO_DEFAULT_SPI_RX_PIN
#define PICO_DEFAULT_SPI_RX_PIN 16
#endif
#ifndef PICO_DEFAULT_SPI_CSN_PIN
#define PICO_DEFAULT_SPI_CSN_PIN 17
#endif

// --- FLASH ---

#define PICO_BOOT_STAGE2_CHOOSE_W25Q080 1

#ifndef PICO_FLASH_SPI_CLKDIV
#define PICO_FLASH_SPI_CLKDIV 2
#endif

// pico_cmake_set_default PICO_FLASH_SIZE_BYTES = (16 * 1024 * 1024)
#ifndef PICO_FLASH_SIZE_BYTES
#define PICO_FLASH_SIZE_BYTES (16 * 1024 * 1024)
#endif

// Drive high to force power supply into PWM mode (lower ripple on 3V3 at light loads)
// no PICO_SMPS_MODE_PIN

// The GPIO Pin used to read VBUS to determine if the device is battery powered.
// no PICO_VBUS_PIN

// The GPIO Pin used to monitor VSYS. Typically you would use this with ADC.
// There is an example in adc/read_vsys in pico-examples.
// no PICO_VSYS_PIN


// pico_cmake_set_default PICO_RP2350_A2_SUPPORTED = 1
#ifndef PICO_RP2350_A2_SUPPORTED
#define PICO_RP2350_A2_SUPPORTED 1
#endif

// cyw43 SPI pins can't be changed at runtime
#ifndef CYW43_PIN_WL_DYNAMIC
#define CYW43_PIN_WL_DYNAMIC 0
#endif

// gpio pin to power up the cyw43 chip
#ifndef CYW43_DEFAULT_PIN_WL_REG_ON
#define CYW43_DEFAULT_PIN_WL_REG_ON 23u
#endif

// gpio pin for spi data out to the cyw43 chip
#ifndef CYW43_DEFAULT_PIN_WL_DATA_OUT
#define CYW43_DEFAULT_PIN_WL_DATA_OUT 24u
#endif

// gpio pin for spi data in from the cyw43 chip
#ifndef CYW43_DEFAULT_PIN_WL_DATA_IN
#define CYW43_DEFAULT_PIN_WL_DATA_IN 24u
#endif

// gpio (irq) pin for the irq line from the cyw43 chip
#ifndef CYW43_DEFAULT_PIN_WL_HOST_WAKE
#define CYW43_DEFAULT_PIN_WL_HOST_WAKE 24u
#endif

// gpio pin for the spi clock line to the cyw43 chip
#ifndef CYW43_DEFAULT_PIN_WL_CLOCK
#define CYW43_DEFAULT_PIN_WL_CLOCK 29u
#endif

// gpio pin for the spi chip select to the cyw43 chip
#ifndef CYW43_DEFAULT_PIN_WL_CS
#define CYW43_DEFAULT_PIN_WL_CS 25u
#endif

#endif