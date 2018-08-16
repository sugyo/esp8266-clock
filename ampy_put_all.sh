#!/bin/sh

SRCS="boot.py config.py digital_clock.py HT16K33.py main.py sta_network.py wifi_off.py"

for src in $SRCS; do
    echo $src
    ampy put $src
done
