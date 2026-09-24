#!/usr/bin/env python3
"""Builds ~/perfmon/report.html from the CSV logs. Run any time: python3 ~/perfmon/report.py"""
import csv, json, os, statistics, webbrowser
from collections import defaultdict
D = os.path.expanduser("~/perfmon")
sysrows = list(csv.DictReader(open(f"{D}/data/system.csv")))
def col(k): return [float(r[k]) for r in sysrows if r[k] != ""]
def pct(v, p): v = sorted(v); return v[min(len(v) - 1, int(len(v) * p))]
def stats(k): v = col(k); return dict(avg=round(statistics.mean(v), 1), p95=round(pct(v, .95), 1), max=max(v))

S = {k: stats(k) for k in ["cpu_total", "ram_used_gb", "swap_gb", "mem_pressure_pct", "compressed_gb"]}
hours = len(sysrows) * 60 / 3600
procs = defaultdict(lambda: [0, 0.0, 0, 0])   # peak_ram, peak_cpu, sum_cpu, samples
for r in csv.DictReader(open(f"{D}/data/processes.csv")):
    p = procs[r["process"]]; c, m = float(r["cpu_pct"]), int(r["ram_mb"])
    p[0] = max(p[0], m); p[1] = max(p[1], c); p[2] += c; p[3] += 1
by_ram = sorted(procs.items(), key=lambda x: -x[1][0])[:15]
by_cpu = sorted(procs.items(), key=lambda x: -x[1][2])[:15]
step = max(1, len(sysrows) // 2000)           # downsample for the chart
pts = sysrows[::step]
total = float(sysrows[0]["ram_total_gb"])
peak_need = S["ram_used_gb"]["max"] + S["swap_gb"]["max"]
verdict = ("16 GB would be tight – get 24 GB+" if peak_need > 14 else
           "16 GB is enough" if peak_need > 7 else "8 GB would work, 16 GB comfortable")
tbl = lambda rows, f: "".join(f"<tr><td>{n}</td>{f(v)}</tr>" for n, v in rows)
html = f"""<!doctype html><meta charset=utf-8><title>Mac usage report</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4"></script>
<style>body{{font:14px -apple-system,sans-serif;max-width:1000px;margin:24px auto;padding:0 16px}}
.k{{display:flex;gap:12px;flex-wrap:wrap}}.k div{{background:#f2f2f5;border-radius:10px;padding:12px 16px}}
b{{font-size:22px;display:block}}table{{border-collapse:collapse;width:100%}}td,th{{padding:4px 8px;border-bottom:1px solid #ddd;text-align:left}}</style>
<h1>Mac usage report</h1><p>{sysrows[0]['time']} → {sysrows[-1]['time']} · {hours:.1f} h logged · machine RAM {total} GB</p>
<div class=k>
<div>CPU avg / p95 / max<b>{S['cpu_total']['avg']} / {S['cpu_total']['p95']} / {S['cpu_total']['max']} %</b></div>
<div>RAM used avg / p95 / max<b>{S['ram_used_gb']['avg']} / {S['ram_used_gb']['p95']} / {S['ram_used_gb']['max']} GB</b></div>
<div>Swap max<b>{S['swap_gb']['max']} GB</b></div>
<div>Mem pressure max<b>{S['mem_pressure_pct']['max']} %</b></div>
<div>Peak need (RAM+swap)<b>{peak_need:.1f} GB</b></div></div>
<h2>Verdict: {verdict}</h2>
<canvas id=c height=110></canvas><canvas id=m height=110></canvas>
<h2>Top processes by peak RAM</h2><table><tr><th>Process<th>Peak RAM MB<th>Peak CPU %</tr>{tbl(by_ram, lambda v: f"<td>{v[0]}<td>{v[1]}")}</table>
<h2>Top processes by total CPU time</h2><table><tr><th>Process<th>Avg CPU % when in top<th>Peak CPU %</tr>{tbl(by_cpu, lambda v: f"<td>{v[2]/v[3]:.1f}<td>{v[1]}")}</table>
<p><small>CPU % per process: 100% = one core fully used.</small></p>
<script>const L={json.dumps([r['time'] for r in pts])};
const ds=(k,l)=>({{label:l,data:{json.dumps({k:[float(r[k] or 0) for r in pts] for k in ['cpu_total','ram_used_gb','swap_gb','compressed_gb']})}[k],pointRadius:0,borderWidth:1}});
new Chart(c,{{type:'line',data:{{labels:L,datasets:[ds('cpu_total','CPU %')]}},options:{{scales:{{x:{{display:false}}}}}}}});
new Chart(m,{{type:'line',data:{{labels:L,datasets:[ds('ram_used_gb','RAM used GB'),ds('compressed_gb','Compressed GB'),ds('swap_gb','Swap GB')]}},options:{{scales:{{x:{{display:false}}}}}}}});</script>"""
open(f"{D}/report.html", "w").write(html)
print("report ->", f"{D}/report.html"); webbrowser.open(f"file://{D}/report.html")
