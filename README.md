# Performance Monitor

A lightweight CPU / RAM logger for macOS. It runs in the background for a week and then shows you how much memory and CPU your real work needs. I built it to decide what to buy when switching Macs.

It uses only the Python standard library and built-in macOS tools (`top`, `vm_stat`, `sysctl`, `memory_pressure`, `ps`), so there's nothing to install.

## What it logs (every 60 s)

- **CPU**: total %, split into user and system time, plus the load average
- **RAM**: memory used (same as Activity Monitor), with app, wired and compressed memory broken out
- **Swap** and **memory pressure**: the signals that show whether a machine is actually short on RAM
- **Top processes**: the 5 using the most CPU and the 5 using the most RAM

Data goes to `data/system.csv` and `data/processes.csv`. Both are git-ignored because they list the apps you run.

## Setup

```bash
git clone https://github.com/Ksawery-Kida/Performance-Monitor.git ~/perfmon
sed "s#__HOME__#$HOME#g" ~/perfmon/com.perfmon.plist.template > ~/Library/LaunchAgents/com.ksawery.perfmon.plist
launchctl load ~/Library/LaunchAgents/com.ksawery.perfmon.plist
```

It starts right away, starts again after a reboot or crash, and stops by itself after 8 days (change `STOP_AFTER_DAYS` in `monitor.py`). The paths assume the repo is cloned to `~/perfmon`.

## Usage

```bash
python3 ~/perfmon/report.py                                        # build and open the HTML report
launchctl list | grep perfmon                                      # check that it's running
launchctl unload ~/Library/LaunchAgents/com.ksawery.perfmon.plist  # stop it
```

The report shows CPU and RAM charts over time, the average, 95th percentile and peak for each, the heaviest processes, and a verdict on how much RAM you need.

**Reading it:** look at **peak RAM + swap** and **max memory pressure**, not "RAM used". macOS fills spare RAM with cache anyway, so a full RAM bar doesn't mean you're running out.
