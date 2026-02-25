import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np

# Use Arial font and slightly larger default font size for report-quality figures
plt.rcParams["font.family"] = "Arial"
plt.rcParams["font.size"] = 12
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np

csv_path = "TAM_335_Lab_8_data.csv"

df = pd.read_csv(csv_path)

col_h = '_H_(head above the crest)'
col_q = 'Q(m3/s)'

bin_min = 0.005
bin_max = 0.0446
bins = np.linspace(bin_min, bin_max, 6)

df['h_bin'] = pd.cut(df[col_h], bins=bins)

# Create the box plot
plt.figure(figsize=(10, 6))
ax = sns.boxplot(x='h_bin', y=col_q, data=df)

# Customize y-axis ticks
ax.yaxis.set_major_locator(ticker.MaxNLocator(15))
plt.grid(True, axis='y', linestyle='--', alpha=0.7)

# Customize labels and title
plt.title("Similarity Study of Overflow Spillways, Lab 8", fontsize=14)
plt.xlabel("ΔH (head above the crest) bin (m)", fontsize=13)
plt.ylabel("Q (m³/s)", fontsize=13)

# Slightly increase tick label font sizes
ax.tick_params(axis="both", labelsize=11)
plt.tight_layout()
plt.savefig("Lab_8_binned_boxplot.png")
plt.show()