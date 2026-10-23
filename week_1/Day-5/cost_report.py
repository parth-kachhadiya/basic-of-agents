"""
cost_report.py - summary of logs/calls.jsonl + latency KDE graph (dark theme).

Install first:  uv add seaborn matplotlib
Run:            uv run python cost_report.py
The graph is only shown in a window. It is never saved to disk.
"""
import json

import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns

LOG_FILE = "logs/calls.jsonl"

USD_TO_INR = 94.97

total_cost = total_in = total_out = 0.0
latencies = []
merged_lines = 0

# Read every JSON record, even if two records ended up on the same line
decoder = json.JSONDecoder()
with open(LOG_FILE, encoding="utf-8") as f:
    for line_no, line in enumerate(f, 1):
        line, pos, found = line.strip(), 0, 0
        while pos < len(line):
            try:
                r, pos = decoder.raw_decode(line, pos)
            except json.JSONDecodeError as e:
                print(f"Skipping unreadable data on line {line_no}: {e}")
                break
            found += 1
            total_cost += float(r["cost_usd"])  # cost_usd is stored as text like "0.000039"
            total_in += r["input_tokens"]
            total_out += r["output_tokens"]
            latencies.append(r["latency_s"])
            while pos < len(line) and line[pos].isspace():
                pos += 1
        if found > 1:
            merged_lines += 1

if merged_lines:
    print(f"Note: {merged_lines} line(s) had two records glued together. Both were still counted.")

calls = len(latencies)
if calls == 0:
    raise SystemExit("No calls logged yet.")

mean = np.mean(latencies)
p50, p95 = np.percentile(latencies, [50, 95])

print(f"Calls:            {calls}")
print(f"Input tokens:     {int(total_in)}")
print(f"Output tokens:    {int(total_out)}")
print(f"Total cost (USD): ${total_cost:.6f}")
print(f"Total cost (INR): ₹{total_cost * USD_TO_INR:.6f}")
print(f"Latency:          mean {mean:.2f}s | p50 {p50:.2f}s | p95 {p95:.2f}s | "
      f"min {min(latencies):.2f}s | max {max(latencies):.2f}s")

if len(set(latencies)) < 2:
    raise SystemExit("Need at least 2 different latency values to draw a distribution.")

# ---------------------------------------------------------------
# Latency KDE graph, dark theme (shown on screen only, not saved)
# ---------------------------------------------------------------
BG, PANEL = "#0B1220", "#111A2E"
TEXT, MUTED, GRID = "#E5E7EB", "#9CA3AF", "#26324A"
CYAN, GREEN, RED = "#38BDF8", "#34D399", "#FB7185"

sns.set_theme(style="dark", rc={
    "figure.facecolor": BG, "axes.facecolor": PANEL, "axes.edgecolor": GRID,
    "axes.labelcolor": TEXT, "text.color": TEXT,
    "xtick.color": MUTED, "ytick.color": MUTED, "grid.color": GRID,
})
fig, ax = plt.subplots(figsize=(10, 5.5))

# The KDE curve (cut=0 keeps it inside the real min/max, no negative latency)
sns.kdeplot(latencies, fill=True, alpha=0.18, color=CYAN, linewidth=0,
            bw_adjust=1.0, cut=0, ax=ax)                    # soft fill under the curve
sns.kdeplot(latencies, fill=False, color=CYAN, linewidth=2.5,
            bw_adjust=1.0, cut=0, ax=ax)                    # the curve line itself

# Shade the slowest 5% (beyond p95) under the same curve
x, y = ax.lines[0].get_data()
tail = x >= p95
ax.fill_between(x[tail], y[tail], color=RED, alpha=0.35, linewidth=0)

# p50 and p95 lines, labelled directly (no legend needed)
ax.set_ylim(0, ax.get_ylim()[1] * 1.2)
top = ax.get_ylim()[1]
ax.axvline(p50, color=GREEN, linestyle="--", linewidth=2)
ax.text(p50 + 0.015, top * 0.96, f"p50  {p50:.2f}s", color=GREEN,
        ha="left", va="top", fontweight="bold")
ax.axvline(p95, color=RED, linestyle="--", linewidth=2)
ax.text(p95 + 0.015, top * 0.96, f"p95  {p95:.2f}s", color=RED,
        ha="left", va="top", fontweight="bold")

# Small summary box
summary = (f"Calls  {calls}\nMean  {mean:.2f}s\n"
           f"Min  {min(latencies):.2f}s\nMax  {max(latencies):.2f}s")
ax.text(0.98, 0.66, summary, transform=ax.transAxes, ha="right", va="top",
        fontsize=10, color=MUTED, linespacing=1.6,
        bbox={"boxstyle": "round,pad=0.6", "facecolor": BG, "edgecolor": GRID})

ax.set_xlabel("Latency per call (seconds)")
ax.set_ylabel("Density")
ax.set_yticks([])  # density numbers are not meaningful to read
ax.grid(axis="x", alpha=0.5)
sns.despine(ax=ax, left=True)

fig.suptitle("LLM call latency distribution", fontsize=15, fontweight="bold", y=0.97)
fig.text(0.5, 0.905, "Red area = slowest 5% of calls", ha="center", fontsize=10, color=MUTED)
fig.subplots_adjust(top=0.84)

plt.show()