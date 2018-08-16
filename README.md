# ESP8266 Clock

## Hardware

* Micropython ESP-WROOM-02D
* adafruit Red 7-segment clock display
* Registors:
  * 10K x3
* Ceramic capacitors:
  * 0.1uF
* 3.3V power supply
* USB to TTL convertor

~~~
           3v3                     3v3             3v3
           ---                     ---             ---
            |   +-----------+       |               |   +--------+
            +---|3v3     RST|-[10K]-+               +---|3v3     |
USB to TTL      |           |          3v3              |        |
convertor       |        IO0|--->SDA   ---       IO0<---|SDA     |
         RXD<---|TXD        |           |               |        |
                |        IO2|--->SCL  [10K]      IO2<---|SCL     |
         TXD<---|RXD        |           |               |        |
                |         EN|-----------+           +---|GND     |
                |           |           |           |   +--------+
            +---|GND    IO15|-[10K]-+  --- 0.1uF    |   adafruit 7-segment
            |   +-----------+       |  ---         ---  clock display
            |   ESP-WROOM-02D       |   |           -
           ---                     --- ---         GND
            -                       -   -
           GND                     GND GND

~~~
