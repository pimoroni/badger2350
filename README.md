# Badger 2350<!-- omit in toc -->
 
A huge upgrade from the original Badger - launched four years ago - the new e-paper display delivers four crisp shades of grey for sharper images and clearer text.

![Badger 2350 front](https://badgewa.re/static/images/badger_web_front.png)

- [Specs](#specs)
- [Meet The Badgeware Family](#meet-the-badgeware-family)
- [Help](#help)
  - [Updating/Reflashing Firmware](#updatingreflashing-firmware)
  - [Installing Apps](#installing-apps)
  - [API Documentation](#api-documentation)

## Specs

* 2.7" 264×176 greyscale e-paper display
* RP2350 + 16MB flash + 8MB PSRAM
* WiFi + Bluetooth 5.2
* USB-C + 1,000mAh battery
* User + system buttons
* Four-zone rear lighting
* "Den Tester" lanyard

## Meet The Badgeware Family

* [Badger](https://github.com/pimoroni/badger2350) - 2.7" 264×176 greyscale e-paper
* [Blinky](https://github.com/pimoroni/blinky2350) - 872 pixel LED display
* [Tufty](https://github.com/pimoroni/tufty2350) - 2.8" 320×240 full-colour IPS LCD

More details at [https://badgewa.re](https://badgewa.re)

## Help

### Updating/Reflashing Firmware

:warning: Our firmware comes in two flavours: 

1. `badger-vX.X.X-micropython-with-filesystem` which will replace all the apps and software on your device with the defaults, and 

2. `badger-vX.X.X-micropython.uf2` which will replace only the firmware.

Pick your desired firmware image from the latest release at [https://github.com/pimoroni/badger2350/releases/latest](https://github.com/pimoroni/badger2350/releases/latest)

Then:

* Connect your badge to your computer with a USB Type-C to USB A cable.
* Turn your badge around so the back is facing you.
* Press and hold the BOOT button towards the far left.
* Briefly tap the RESET button to the right of BOOT.
* A disk named "RP2350" should appear on your computer.
* Drag and drop the firmware .uf2 onto this disk.
* Your badge should update and reboot into the menu!

### Installing Apps

* Connect your badge to your computer with a USB Type-C to USB A cable.
* Turn your badge around so the back is facing you.
* Double-tap the RESET button, located toward the right on the left-hand side of the badge.
* A disk named "Badger2350" should appear on your computer.
* Copy your app directory into /system/apps.
* *Safely Unmount* the disk from your computer. This may take a second.
* Your badge should reboot into the menu!

### API Documentation

For comprehensive documentation of the Badgeware API, see: [https://badgewa.re/docs](https://badgewa.re/docs)