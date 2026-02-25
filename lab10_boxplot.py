import seaborn as sns
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker

# Use Arial font and slightly larger default font size for report-quality figures
plt.rcParams["font.family"] = "Arial"
plt.rcParams["font.size"] = 12

# Lab 10 data
data = [0.00576, 0.00148, 0.00212, 0.00352, 0.00241, 0.00477]

# Create plot
plt.figure(figsize=(10, 4))
ax = sns.boxplot(x=data)

# Customize x-axis ticks
ax.xaxis.set_major_locator(ticker.MaxNLocator(15))
plt.grid(True, axis='x', linestyle='--', alpha=0.7)

# Labels with slightly larger font sizes
plt.title("Open-Channel Flow, Lab 10", fontsize=14)
plt.xlabel("Q(m3/s) - flow rate", fontsize=13)
plt.ylabel("Lab 10 Flow Rates", fontsize=13)

# Slightly increase tick label font sizes
ax.tick_params(axis="both", labelsize=11)

plt.savefig("lab10_boxplot.png")
plt.show()
