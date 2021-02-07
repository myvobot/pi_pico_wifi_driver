# MicroPython Raspberry Pi Pico WiFi Driver

- This project was forked and modified from: https://github.com/kfricke/micropython-esp8266uart
- This driver for MicroPython intends to be useable on any MicroPython platform which implements a serial UART interface.
- I tested this on Raspberry Pi Pico, together with an ESP-01 module (with AT command UART interface).
- Since Pi-Pico has no radio built-in, it is good to get a cheap WiFi module like ESP-01 for it.

```
+-------------------+                +-------------------+
|                   |                |                   |
|   Raspberry Pi    |                |      ESP-01       |
|      Pico         |                |                   |
|                   |                |                   |
|               IO4 +----------------> RXD               |
|                   |                |                   |
|               IO5 <----------------+ TXD               |
|                   |                |                   |
|               GND +----------------+ GND               |
|                   |                |                   |
|                   |                |                   |
|      HOST         |                |    WIFI MODULE    |
|                   |                |                   |
|   (MicroPython)   |                |   (AT Firmware)   |
|                   |                |                   |
+-------------------+                +-------------------+
```

## Usage

- Upload these script files onto your Pico board, using Thonny or mpfs, etc.:
    - `esp_at_uart.py`
    - `uart_timeout_any.py`
    - `test.py`

- On the repl shell, run with:

```
import test
```

## Note

- So far there is no "timeout" for uart's read/readline, thus we have to use "uart_timeout_any" as a temporally hotfix. `https://github.com/raspberrypi/micropython/blob/pico/ports/rp2/machine_uart.c`

- It seems the Pi Pico is quite slow in processing incoming UART bytes, and we are unable to set the RX buffer at this moment. So we lost some bytes while receiving bulk message from ESP-01, a quick fix here is to set the ESP-01 to use 9600bps instead. You may connect the ESP-01 to your PC's console and use "AT+UART_DEF=9600,8,1,0,0" to setup it first (default to 115200bps).



