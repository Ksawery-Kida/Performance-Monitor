#!/usr/bin/env python3
"""Samples CPU / RAM / swap / memory pressure every INTERVAL seconds into CSV files.
Standard library only. Runs under launchd (see com.ksawery.perfmon.plist)."""
import csv, datetime, os, re, subprocess, time

INTERVAL = 60          # seconds between samples
TOP_N = 5              # top processes logged per sample
STOP_AFTER_DAYS = 8    # auto-stop safety net
DIR = os.path.expanduser("~/perfmon/data")
os.makedirs(DIR, exist_ok=True)
START = time.time()

def sh(cmd):
    return subprocess.run(cmd, capture_output=True, text=True).stdout

def cpu():
    # 2 samples 1s apart; the 2nd one is the real current usage
    out = sh(["top", "-l", "2", "-n", "0", "-s", "1"])
    m = re.findall(r"CPU usage: ([\d.]+)% user, ([\d.]+)% sys, ([\d.]+)% idle", out)[-1]
    load = re.findall(r"Load Avg: ([\d.]+)", out)[-1]
    return float(m[0]), float(m[1]), round(100 - float(m[2]), 1), float(load)

def memory():
    total = int(sh(["sysctl", "-n", "hw.memsize"]))
    vm = sh(["vm_stat"])
    page = int(re.search(r"page size of (\d+)", vm).group(1))
    g = lambda k: int(re.search(rf"{k}:\s+(\d+)", vm).group(1)) * page
    app = g("Anonymous pages") - g("Pages purgeable")
    wired = g("Pages wired down")
    comp = g("Pages occupied by compressor")
    used = app + wired + comp            # ~ Activity Monitor "Memory Used"
    swap = re.search(r"used = ([\d.]+)M", sh(["sysctl", "-n", "vm.swapusage"]))
    free_pct = re.search(r"free percentage: (\d+)", sh(["memory_pressure", "-Q"]))
    GB = 1024 ** 3
    return (round(total / GB, 1), round(used / GB, 2), round(app / GB, 2), round(wired / GB, 2),
            round(comp / GB, 2), round(float(swap.group(1)) / 1024, 2) if swap else 0,
            100 - int(free_pct.group(1)) if free_pct else "")

def procs():
    rows = []
    for line in sh(["ps", "-Ao", "pcpu=,rss=,comm="]).splitlines():
        p = line.split(None, 2)
        if len(p) == 3:
            rows.append((float(p[0]), int(p[1]) / 1024, os.path.basename(p[2])))
    return rows

def append(name, header, rows):
    path = os.path.join(DIR, name)
    new = not os.path.exists(path)
    with open(path, "a", newline="") as f:
        w = csv.writer(f)
        if new: w.writerow(header)
        w.writerows(rows)

while time.time() - START < STOP_AFTER_DAYS * 86400:
    t0 = time.time()
    try:
        ts = datetime.datetime.now().isoformat(timespec="seconds")
        u, s, busy, load = cpu()
        total, used, app, wired, comp, swap, pressure = memory()
        append("system.csv",
               ["time", "cpu_user", "cpu_sys", "cpu_total", "load1", "ram_total_gb", "ram_used_gb",
                "app_gb", "wired_gb", "compressed_gb", "swap_gb", "mem_pressure_pct"],
               [[ts, u, s, busy, load, total, used, app, wired, comp, swap, pressure]])
        p = procs()
        top = {x[2]: x for x in sorted(p, reverse=True)[:TOP_N]}
        top.update({x[2]: x for x in sorted(p, key=lambda x: -x[1])[:TOP_N]})
        append("processes.csv", ["time", "process", "cpu_pct", "ram_mb"],
               [[ts, n, c, round(r)] for c, r, n in top.values()])
    except Exception as e:
        print(datetime.datetime.now(), "error:", e, flush=True)
    time.sleep(max(0, INTERVAL - (time.time() - t0)))
