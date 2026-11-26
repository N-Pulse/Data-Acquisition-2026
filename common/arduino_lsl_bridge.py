#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Work out what each comma-separated field of the board's serial output is.

Reads lines for a few seconds, then for every field prints min / max / mean /
std / number of distinct values and a hint:
  - constant              -> a flag or fixed value, not a channel
  - counter (+1 per line) -> sample counter
  - increasing            -> timestamp (shows the rate it implies if in us or ms)
  - varies                -> channel-like
  - stuck at one value    -> channel that is unplugged or saturated

It also prints the real line rate measured with the PC clock (independent of
whatever the firmware says).

Tip: run it twice, once with the arm relaxed and once squeezing the fist, and
compare the std of the channels: the channels on the forearm should jump.

Close the bridge first (the COM port can only be open once).

Usage:
    python profile_fields.py
    python profile_fields.py --port COM5 --seconds 8
"""
import argparse
import statistics
import time
from collections import Counter


def analyse(rows, elapsed):
    if not rows:
        print("No valid lines received.")
        return

    n_fields = Counter(len(r) for r in rows).most_common(1)[0][0]
    rows = [r for r in rows if len(r) == n_fields]
    print(f"{len(rows)} lines with {n_fields} fields in {elapsed:.2f} s "
          f"-> {len(rows) / elapsed:.1f} lines/s (PC clock)\n")

    print(f"{'field':>5} {'min':>10} {'max':>10} {'mean':>12} {'std':>10} {'distinct':>9}  hint")
    for j in range(n_fields):
        col = [r[j] for r in rows]
        diffs = [b - a for a, b in zip(col, col[1:])]
        distinct = len(set(col))
        hint = ""
        if distinct == 1:
            hint = f"constant ({col[0]})"
        elif diffs and sum(d == 1 for d in diffs) / len(diffs) > 0.99:
            hint = "counter (+1 per line)"
        elif diffs and sum(d > 0 for d in diffs) / len(diffs) > 0.99:
            step = statistics.median(diffs)
            if step > 0:
                hint = (f"increasing, median step {step:g} -> "
                        f"{1e6 / step:.1f} Hz if us, {1e3 / step:.1f} Hz if ms")
            else:
                hint = "increasing"
        else:
            hint = "varies (channel-like)"
        print(f"{j:>5} {min(col):>10} {max(col):>10} {statistics.fmean(col):>12.1f} "
              f"{statistics.pstdev(col):>10.1f} {distinct:>9}  {hint}")


def main():
    import serial  # imported here so analyse() can be tested without pyserial

    parser = argparse.ArgumentParser()
    parser.add_argument("--port", default="COM12")
    parser.add_argument("--baud", type=int, default=250000)
    parser.add_argument("--seconds", type=float, default=5.0)
    args = parser.parse_args()

    ser = serial.Serial(args.port, args.baud, timeout=0.1)
    time.sleep(0.5)
    ser.reset_input_buffer()
    ser.readline()  # discard first (probably partial) line

    rows = []
    t0 = time.time()
    while time.time() - t0 < args.seconds:
        raw = ser.readline()
        if not raw.endswith(b"\n"):
            continue
        try:
            rows.append([int(x) for x in raw.decode("ascii").strip().split(",")])
        except (UnicodeDecodeError, ValueError):
            continue
    elapsed = time.time() - t0
    ser.close()

    analyse(rows, elapsed)


if __name__ == "__main__":
    main()