#!/usr/bin/env python

from queue import Queue
from random import randrange
from time import sleep
import re

from tqdm import tqdm

DIMM = 0.7

class RGB:
    def __init__(self, r, g, b):
        self.values = (r, g, b)

    def __str__(self):
        return '\x1b[38;2;%d;%d;%dm' % self.values

    def __add__(self, other):
        if isinstance(other, RGB):
            values = [s + o for s, o in zip(self.values, other.values)]
            return RGB(*values)
        elif isinstance(other, str):
            return str(self) + other

    def __truediv__(self, other):
        values = [s / other for s in self.values]
        return RGB(*values)

class IterQueue(object):
    pb = None  # to be overrided by handler
    def __init__(self, queue):
        self.queue = queue

    def __iter__(self):
        done = 0
        while self.queue.qsize():
            try:
                yield self.queue.get_nowait()
                done += 1
                self.pb.total = done + self.queue.qsize()
            except:
                raise


B = "\x1b[1m" # Bright
C = "\x1b[0m" # Clear
GREEN = RGB(220, 100, 100)
RED = RGB(100, 220, 100)
BLUE = RGB(100, 100, 220)
W = RGB(255, 255, 255) # White
GREY = RGB(150, 150, 150)

RE_RGB = re.compile(r'\x1b\[38;2;(\d+);(\d+);(\d+)m')


def _dimmer(match):
    r, g, b = match.groups()
    return str(RGB(int(int(r) * DIMM), int(int(g) * DIMM), int(int(b) * DIMM)))


def bar(iterable, desc=None, leave=None, color=RGB(100, 220, 80), **kwargs):
    if desc is not None:
        kwargs["desc"] = desc

    settings = dict(
        ncols=80,
        bar_format=f'{B}{{desc}} {{bar}}{C} {B}{RED}{{percentage:3.0f}}% {W}eta \x1b[36m{{remaining}}{C}',
        leave=leave,
        ascii=[
            GREY + "━",
            color + "━",
            ],
    )
    settings.update(kwargs)
    if isinstance(iterable, Queue):
        iterable = IterQueue(iterable)
        pb = tqdm(iterable, total=iterable.queue.qsize(), **settings)
        iterable.pb = pb
    else:
        pb = tqdm(iterable, **settings)
    pbclose = pb.close
    def close():
        pb.bar_format = pb.bar_format.replace(B, "")
        pb.bar_format = RE_RGB.sub(_dimmer, pb.bar_format)
        for i, s in enumerate(pb.ascii):
            pb.ascii[i] = s.replace(B, "")
            pb.ascii[i] = RE_RGB.sub(_dimmer, pb.ascii[i])
        return pbclose()
    pb.close = close
    return pb

if __name__ == "__main__":

    print("simple in series pbs")
    for i1 in bar(range(40), "a values"):
        sleep(0.05)
    for i2 in bar(range(40), "b values"):
        sleep(0.05)
    for i2 in bar(range(40), "c values"):
        sleep(0.05)

    print("rainbow in series pbs")
    for i2 in bar(range(40), "c values", color=RED):
        sleep(0.05)
    for i2 in bar(range(40), "c values", color=(RED+GREEN)/2):
        sleep(0.05)
    for i1 in bar(range(40), "a values", color=GREEN):
        sleep(0.05)
    for i1 in bar(range(40), "a values", color=(GREEN+BLUE)/2):
        sleep(0.05)
    for i2 in bar(range(40), "b values", color=BLUE):
        sleep(0.05)

    print("nested pbs")
    for i1 in bar(range(10), "a values"):
        for i2 in bar(range(10), "b values"):
            sleep(0.05)

    print("iter over a queue (eta gets updated when new elements are added)")
    queue = Queue()
    for i in range(10):
        queue.put(i)
    for i1 in bar(queue, "growing queue"):
        for i2 in bar(range(10), "sub values"):
            sleep(0.05)
        if i1 % 3 == 0:
            for i in range(10):
                queue.put(1)
