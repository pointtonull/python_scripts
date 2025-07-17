#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.13"
# dependencies = [
#   "diskcache",
# ]
# ///

from subprocess import Popen, PIPE
import curses
import os
import sys
import time
import re

from diskcache import Cache

CACHE = Cache("~/.cache/memtop")
PAUSE = 15
MiB = 1024**2

REPLACEMENTS = [
    (re.compile(r"firefox.*|plugin-container.*", re.IGNORECASE), "firefox"),
    (re.compile(r"google drive.*", re.IGNORECASE), "google drive"),
    (re.compile(r"spotify.*", re.IGNORECASE), "spotify"),
    (re.compile(r"steam.*", re.IGNORECASE), "steam"),
    (re.compile(r"[\.\w]*\.(\w*)", re.IGNORECASE), r"\1"),
    (re.compile(r"mpv.*", re.IGNORECASE), "smplayer"),
    (re.compile(r"backend", re.IGNORECASE), "docker"),
]

def get_total_mem_bytes():
    try:
        vm_stat = Popen("sysctl -n hw.memsize", shell=True, stdout=PIPE)
        output, _ = vm_stat.communicate()
        return int(output.strip())
    except Exception:
        return 8 * 1024**3  # fallback to 8 GiB

TOTAL_MEM_BYTES = get_total_mem_bytes()

def get_ps_procs() -> dict:
    proc = Popen("ps -cxw -o pid,pmem,comm", shell=True, stdout=PIPE, stderr=PIPE)
    stdout, stderr = proc.communicate()
    if stderr:
        return {}
    stdout = stdout.decode()
    procs = stdout.splitlines()
    header = procs.pop(0)
    fields = header.split()
    command_pos = header.find(fields[-1])
    output = {}
    for proc in procs:
        values = proc[:command_pos].split()
        values.append(proc[command_pos:])
        proc = dict(zip(fields, values))
        try:
            output[int(proc["PID"])] = proc
        except KeyError:
            print(proc)
    return output


def get_pids_linux():
    return (int(i) for i in os.listdir("/proc") if i.isdigit())


def get_pids_darwin(proc_table):
    return proc_table.keys()


def get_pids(proc_table):
    if sys.platform == "darwin":
        return get_pids_darwin(proc_table)
    else:
        return get_pids_linux()


def get_mem_linux(pid):
    try:
        with open(f"/proc/{pid}/statm") as file:
            memory = file.read().split()[0]
            return int(memory) * 4096 / MiB  # Convert to MiB
    except Exception:
        return 0


def get_mem_darwin(pid, proc_table):
    proc = proc_table.get(pid)
    if proc:
        mem_percent = float(proc["%MEM"])
        mem_bytes = TOTAL_MEM_BYTES * mem_percent / 100
        return mem_bytes / MiB
    return 0


def get_mem(pid, proc_table):
    if sys.platform == "darwin":
        return get_mem_darwin(pid, proc_table)
    else:
        return get_mem_linux(pid)


def filter_name(name):
    for regex, replacement in REPLACEMENTS:
        name = regex.sub(replacement, name)
    return name.lower()


def get_name_linux(pid):
    try:
        with open(f"/proc/{pid}/stat") as file:
            name = file.read().split("(")[1].split(")")[0]
            return filter_name(name)
    except Exception:
        return None


def get_name_darwin(pid, proc_table):
    proc = proc_table.get(pid)
    if proc:
        name = proc["COMM"]
        return filter_name(name)
    return None


def get_name(pid, proc_table):
    if sys.platform == "darwin":
        return get_name_darwin(pid, proc_table)
    else:
        return get_name_linux(pid)


def main():
    if len(sys.argv) > 1:
        repeat = int(sys.argv[1])
    else:
        repeat = -1

    step = 0
    window = curses.initscr()
    window.nodelay(1)
    curses.curs_set(0)

    try:
        while step != repeat:
            proc_table = get_ps_procs() if sys.platform == "darwin" else None
            pids = list(get_pids(proc_table))
            mem_and_names = []
            for pid in pids:
                mem = get_mem(pid, proc_table)
                name = get_name(pid, proc_table)
                if name:
                    mem_and_names.append((mem, pid, name))

            pidsdict = {}
            total = 0

            for mem, pid, name in mem_and_names:
                total += mem
                if name in pidsdict:
                    pidsdict[name][0] += mem
                else:
                    pidsdict[name] = [mem, pid]

            pidsdict["TOTAL"] = [total, "Sum"]
            sorted_pids = sorted(pidsdict.items(), key=lambda x: x[1][0], reverse=True)

            window.clear()
            pos = 0
            for name, details in sorted_pids[: window.getmaxyx()[0] - 1]:
                try:
                    window.addstr(pos, 0, f"{details[0]:10.2f} MB {name}")
                except curses.error:
                    pass
                pos += 1

            window.refresh()
            time.sleep(PAUSE)
            step += 1
    except KeyboardInterrupt:
        pass
    finally:
        curses.nocbreak()
        window.keypad(False)
        curses.echo()
        curses.endwin()


if __name__ == "__main__":
    main()
