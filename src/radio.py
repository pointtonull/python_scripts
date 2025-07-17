#!/usr/bin/python3
#-*- coding: UTF-8 -*-

from subprocess import Popen, PIPE
from collections import defaultdict
import os
import time

HISTORIAL = os.path.expanduser("~/.radio")


def sintonizar(freq):
    try:
        float(freq)
        freq = "%.4f" % (round(float(freq) / .0625) * .0625)
    except ValueError:
        freq = "off"

    print("» %s" % freq)
    proceso = Popen("fm -T forever %s" % freq, shell=True,
        stdout=PIPE, stderr=PIPE)
    os.system("""amixer -q set Line unmute""")
    proceso.kill()

    with open(HISTORIAL, "a") as file:
        file.write("%d,%s\n" % (time.time(), freq))

    if freq == "off":
        os.system("""amixer -q set Line mute""")
        read_historial()
        print("Radio apagada")


def read_historial():
    with open(HISTORIAL) as file:
        lines = [line.strip().split(",")
            for line in file.readlines()[-200:]]
    lines.append(("%d" % time.time(), "off"))

    favorites = defaultdict(int)
    for index, (seconds, freq) in enumerate(lines[:-1]):
        seconds = int(lines[index + 1][0]) - int(seconds)
        favorites[freq] += seconds

    ranking = []
    total = 0
    for freq, seconds in favorites.iteritems():
        try:
            float(freq)
            ranking.append((seconds, freq))
            total += seconds
        except ValueError:
            pass
    ranking.sort(reverse=True)

    threshold = total * .01
    for pos, (seconds, freq) in enumerate(ranking):
        if seconds > threshold:
            print(" %2d - %s" % (pos + 1, freq))


def get_line():
    try:
        return raw_input("Sintonia: ").strip()
    except EOFError:
        print("Saliendo del sintonizador, se deja la radio encendida")
        return "q"


def main():
    read_historial()
    sintonia = get_line()
    while sintonia not in ("q", "quit"):
        sintonizar(sintonia)
        sintonia = get_line()


if __name__ == "__main__":
    exit(main())
