"""
pump_summary_plot.py
Generates a presentation-ready summary figure comparing pump HP results
across all four pipe configurations:
  2-inch PVC, 2-inch Steel, 3-inch PVC, 3-inch Steel
"""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

# ── Data ──────────────────────────────────────────────────────────────────────
labels = ["2\" PVC", "2\" Steel", "3\" PVC", "3\" Steel"]

velocity        = [2.960, 2.960, 1.316, 1.316]          # m/s
major_losses    = [1.421, 1.788, 0.202, 0.231]          # m
minor_losses    = [7.850, 7.850, 9.178, 9.178]          # m
total_losses    = [9.271, 9.638, 9.380, 9.409]          # m
pump_head       = [11.315, 11.682, 11.066, 11.094]      # m
shaft_power_hp  = [1.273, 1.314, 1.245, 1.248]          # hp
shaft_power_w   = [949.2, 980.0, 928.3, 930.7]          # W

x = np.arange(len(labels))

# ── Style ─────────────────────────────────────────────────────────────────────
COLORS = {
    "2in_PVC":   "#2196F3",   # blue
    "2in_Steel": "#F44336",   # red
    "3in_PVC":   "#4CAF50",   # green
    "3in_Steel": "#FF9800",   # orange
}
bar_colors = list(COLORS.values())

plt.rcParams.update({
    "font.family": "sans-serif",
    "font.size": 11,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.grid": True,
    "axes.grid.axis": "y",
    "grid.alpha": 0.35,
    "grid.linestyle": "--",
})

fig = plt.figure(figsize=(16, 10), facecolor="#F8F9FA")

gs = fig.add_gridspec(2, 3, hspace=0.52, wspace=0.38,
                      left=0.07, right=0.97, top=0.96, bottom=0.10)

# ── Helper ────────────────────────────────────────────────────────────────────
def bar_chart(ax, values, ylabel, title, fmt="{:.3f}", color_list=bar_colors,
              highlight_min=True):
    bars = ax.bar(x, values, color=color_list, width=0.55,
                  edgecolor="white", linewidth=1.2, zorder=3)
    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=10.5)
    ax.set_ylabel(ylabel, fontsize=10)
    ax.set_title(title, fontsize=12, fontweight="bold", pad=8, color="#333333")

    # value labels on bars
    best_idx = np.argmin(values) if highlight_min else np.argmax(values)
    for i, (bar, val) in enumerate(zip(bars, values)):
        ypos = bar.get_height() + (max(values) - min(values)) * 0.02
        weight = "bold" if i == best_idx else "normal"
        color  = "#1a6b1a" if (highlight_min and i == best_idx) else \
                 ("#b71c1c" if (not highlight_min and i == best_idx) else "#333333")
        ax.text(bar.get_x() + bar.get_width() / 2, ypos,
                fmt.format(val), ha="center", va="bottom",
                fontsize=9.5, fontweight=weight, color=color)

    # tighten y-axis
    lo, hi = min(values), max(values)
    span = hi - lo if hi != lo else hi * 0.1
    ax.set_ylim(lo - span * 0.35, hi + span * 0.55)
    ax.yaxis.set_tick_params(labelsize=9)

# ── Panel 1 – Velocity ────────────────────────────────────────────────────────
ax1 = fig.add_subplot(gs[0, 0])
bar_chart(ax1, velocity, "Velocity (m/s)", "Flow Velocity", fmt="{:.3f}",
          highlight_min=True)

# ── Panel 2 – Losses stacked bar ──────────────────────────────────────────────
ax2 = fig.add_subplot(gs[0, 1])
major_arr = np.array(major_losses)
minor_arr = np.array(minor_losses)
b1 = ax2.bar(x, minor_arr, width=0.55, color=bar_colors,
             edgecolor="white", linewidth=1.2, zorder=3, alpha=0.65, label="Minor")
b2 = ax2.bar(x, major_arr, width=0.55, bottom=minor_arr,
             color=bar_colors, edgecolor="white", linewidth=1.2,
             zorder=3, hatch="////", alpha=0.95, label="Major")

for i, (maj, tot) in enumerate(zip(major_losses, total_losses)):
    ax2.text(x[i], tot + 0.08, f"{tot:.2f} m",
             ha="center", fontsize=9.5, fontweight="bold", color="#333333")

ax2.set_xticks(x); ax2.set_xticklabels(labels, fontsize=10.5)
ax2.set_ylabel("Head Loss (m)", fontsize=10)
ax2.set_title("Head Losses\n(Major + Minor)", fontsize=12,
              fontweight="bold", pad=8, color="#333333")
ax2.set_ylim(0, max(total_losses) + 3.2)   # extra headroom for legend inside
ax2.yaxis.set_tick_params(labelsize=9)

# legend inside axes – top-right corner, above the bar labels
patch_minor = mpatches.Patch(facecolor="#888888", alpha=0.65, label="Minor losses")
patch_major = mpatches.Patch(facecolor="#888888", hatch="////", label="Major losses")
ax2.legend(handles=[patch_minor, patch_major], fontsize=9,
           loc="upper right", framealpha=0.85, edgecolor="#cccccc")

# ── Panel 3 – Required Pump Head ─────────────────────────────────────────────
ax3 = fig.add_subplot(gs[0, 2])
bar_chart(ax3, pump_head, "Pump Head (m)", "Required Pump Head",
          fmt="{:.3f}", highlight_min=True)

# draw horizontal line at min to show savings
min_head = min(pump_head)
ax3.axhline(min_head, color="#4CAF50", linewidth=1.4, linestyle="--", zorder=2)

# ── Panel 4 – Shaft Power (W) ─────────────────────────────────────────────────
ax4 = fig.add_subplot(gs[1, 0])
bar_chart(ax4, shaft_power_w, "Shaft Power (W)", "Required Shaft Power (W)",
          fmt="{:.1f}", highlight_min=True)

# ── Panel 5 – Shaft Power (hp) ───────────────────────────────────────────────
ax5 = fig.add_subplot(gs[1, 1])
bar_chart(ax5, shaft_power_hp, "Shaft Power (hp)", "Required Shaft Power (hp)",
          fmt="{:.4f}", highlight_min=True)

# ── Panel 6 – Summary table ───────────────────────────────────────────────────
ax6 = fig.add_subplot(gs[1, 2])
ax6.axis("off")
ax6.set_title("Results Summary", fontsize=12, fontweight="bold",
              pad=8, color="#333333")

col_labels = ["Config", "Head\n(m)", "Power\n(W)", "Power\n(hp)"]
row_data = [
    ["2\" PVC",   f"{pump_head[0]:.3f}", f"{shaft_power_w[0]:.1f}", f"{shaft_power_hp[0]:.4f}"],
    ["2\" Steel", f"{pump_head[1]:.3f}", f"{shaft_power_w[1]:.1f}", f"{shaft_power_hp[1]:.4f}"],
    ["3\" PVC",   f"{pump_head[2]:.3f}", f"{shaft_power_w[2]:.1f}", f"{shaft_power_hp[2]:.4f}"],
    ["3\" Steel", f"{pump_head[3]:.3f}", f"{shaft_power_w[3]:.1f}", f"{shaft_power_hp[3]:.4f}"],
]

table = ax6.table(
    cellText=row_data,
    colLabels=col_labels,
    cellLoc="center",
    loc="center",
    bbox=[0.0, 0.05, 1.0, 0.90],
)
table.auto_set_font_size(False)
table.set_fontsize(10)

# style header row
for j in range(len(col_labels)):
    table[0, j].set_facecolor("#37474F")
    table[0, j].set_text_props(color="white", fontweight="bold")

# highlight best (min power) row – 3in PVC (index 2)
best_row_idx = np.argmin(shaft_power_w) + 1   # +1 for header offset
for j in range(len(col_labels)):
    table[best_row_idx, j].set_facecolor("#C8E6C9")
    table[best_row_idx, j].set_text_props(fontweight="bold", color="#1b5e20")

# color-code config column
for i, color in enumerate(bar_colors):
    table[i + 1, 0].set_facecolor(color)
    table[i + 1, 0].set_text_props(color="white", fontweight="bold")

# footer note
fig.text(0.5, 0.015,
         "Green highlight = lowest power requirement     |     Green dashed line = minimum pump head",
         ha="center", fontsize=13, fontweight="bold", color="#1b5e20")

# ── Save & show ───────────────────────────────────────────────────────────────
out_path = "/Users/amarkoric/Desktop/School/ME 470/ME_470_Programs/pump_summary.png"
plt.savefig(out_path, dpi=180, bbox_inches="tight", facecolor=fig.get_facecolor())
print(f"Saved → {out_path}")
plt.show()
