# Performance Monitor

I'm switching to a new Mac and didn't want to guess how much RAM I actually need, so I wrote this. It logs my CPU and RAM usage in the background for a week, and then I check the peaks.

No dependencies. It's just Python's standard library plus the tools macOS already has (`top`, `vm_stat`, `sysctl`, `memory_pressure`, `ps`).

## What it logs

Once a minute:
- CPU usage (user / sys / total) and load average
- RAM used (the same number Activity Monitor shows), split into app / wired / compressed
- swap and memory pressure
- top 5 processes by CPU and top 5 by RAM

Everything goes into `data/system.csv` and `data/processes.csv`. I don't commit those because they show which apps I run.

## Setup

```bash
git clone https://github.com/Ksawery-Kida/Performance-Monitor.git ~/perfmon
sed "s#__HOME__#$HOME#g" ~/perfmon/com.perfmon.plist.template > ~/Library/LaunchAgents/com.ksawery.perfmon.plist
launchctl load ~/Library/LaunchAgents/com.ksawery.perfmon.plist
```

launchd starts it right away and restarts it after a reboot. It stops by itself after 8 days (`STOP_AFTER_DAYS` in `monitor.py`).

## Usage

```bash
python3 ~/perfmon/report.py                                        # report with charts
launchctl list | grep perfmon                                      # is it running?
launchctl unload ~/Library/LaunchAgents/com.ksawery.perfmon.plist  # stop it
```

One thing I learned: "RAM used" doesn't mean much on macOS because it fills free RAM with cache anyway. The numbers that matter are **peak RAM + swap** and **memory pressure**.
