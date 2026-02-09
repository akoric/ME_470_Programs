# UIUC TAM 335 Lab Data Analysis

This program works with data from past UIUC TAM 335 labs, specifically Lab 8 and Lab 10.

## Overview

**Lab 8: Similarity Study of Overflow Spillways**  
The main goal of this lab is to test dynamic similarity by comparing flow over geometrically similar spillways in a small flume.

**Lab 10: Open-Channel Flow**  
This lab focuses on open-channel flow in a rectangular flume. The whole point is to see how the water surface depth changes along the channel for a fixed slope and flow rate.

---

## Lab 8 Analysis

![Binned Boxplot](binned_boxplot.png)

This figure shows how the measured flow rate (Q) changes as the head above the spillway crest (ΔH) increases in the “Similarity Study of Overflow Spillways” lab (lab 8). The data are grouped into ΔH ranges (bins) along the x-axis, and each boxplot summarizes the distribution of flow rates recorded within that head range.

---

## Lab 10 Analysis

![Lab 10 Boxplot](lab10_boxplot.png)

This figure is a box-and-whisker plot showing the range of volumetric flow rates Q used across several runs of the Open-Channel Flow (Lab 10) experiment. The x-axis is the flow rate in m³/s, and each value represents the single constant discharge used during a full lab run (the same Q is held while the gate settings are changed to create different water-surface profiles).

---

## Max Flow Rate Calculation

![Diagram](Diagram%20-2.jpg)

The diagram above shows the configuration for Lab 10 with the max possible slope of the flume. The Bernoulli equation is applied to find the max possible flow rate in the flume without losses.

Using the data in `Max_Q_with_loss.py` and material properties of the flume, an estimate of the max flow rate using Bernoulli's extended equation notes the following results:

### Equations Solved

The script solves the following system of three equations for velocity ($v_2$), friction factor ($f$), and Reynolds number ($Re_D$):

**Hydraulic Diameter ($D_h$):**

$$ D_h = \frac{4A}{P} = \frac{2HW}{H+W} $$

1. **Extended Bernoulli Equation (Energy Equation):**

$$ (z_1 - z_2) - \frac{v_2^2}{2g} - f \frac{L}{D_h} \frac{v_2^2}{2g} = 0 $$

2. **Reynolds Number Definition:**

$$ Re_D - \frac{\rho v_2 D_h}{\mu} = 0 $$

3. **Haaland Equation (Friction Factor):**

$$ \frac{1}{\sqrt{f}} + 1.8 \log_{10} \left( \left( \frac{\epsilon/D_h}{3.7} \right)^{1.11} + \frac{6.9}{Re_D} \right) = 0 $$

### ==== Results ====
```text
v2 (m/s)   = 1.37621273608829
v2 (ft/s)  = 4.51513379306791

f          = 0.0150296841684291
Re_D       = 239217.544386167

Q (m^3/s)  = 0.0426181156231067
Q (ft^3/s) = 1.50504596779533
Q (GPM)    = 675.509918060928
```

---

## Pump Sizing Reference (Bernoulli + Loss Model)

The analysis in `pump_hp.py` is based on the steady-flow energy equation (Bernoulli with pump head + head losses) and includes both major (friction) and minor (fittings) losses.

### 1. System Overview

Flow is modeled from:
- **Point 1:** Free surface of a large open tank (weigh tank)
- **Point 2:** Outlet of the pipe (discharging to atmosphere)

The pump provides energy to overcome:
- Elevation rise
- Exit velocity
- Losses from pipe friction and fittings

### 2. Key Assumptions

**Fluid assumptions**
- Water at ~20°C (constant properties)
- Incompressible flow
- Steady flow
- Fully filled pipe in all sections

**Pressure assumptions**
- Both point 1 and point 2 are exposed to atmosphere:
  $$ P_1 = P_2 = P_{atm} $$
  So the pressure terms cancel.

**Velocity assumptions**
- At point 1, the tank surface area is very large, so:
  $$ V_1 \approx 0 $$
- At point 2, flow exits a pipe, so:
  $$ V_2 = \frac{Q}{A_{pipe}} $$

### 3. Elevation Reference

We choose point 1 as the elevation reference:
$$ z_1 = 0 $$

Point 2 is higher than point 1 by:
$$ z_2 = 3 \text{ ft} = 0.9144 \text{ m} $$

### 4. Bernoulli / Energy Equation Used

The steady-flow energy equation between points 1 → 2 including pump head and losses is:

$$ \frac{P_1}{\rho g} + z_1 + \frac{V_1^2}{2g} + h_s = \frac{P_2}{\rho g} + z_2 + \frac{V_2^2}{2g} + h_L $$

Since $P_1 = P_2$ and $V_1 \approx 0$, this simplifies to:

$$ h_s = (z_2 - z_1) + \frac{V_2^2}{2g} + h_L $$

### 5. Head Losses Included

Total losses:
$$ h_L = h_{major} + h_{minor} $$

#### 5.1 Minor losses (fittings)

Minor losses are modeled using:
$$ h_{minor} = \sum K_i \frac{V^2}{2g} $$

The current model includes:

| Component | Count | K value |
|---|---|---|
| Tee branch exiting weigh tank | 1 | 1.0 |
| Contraction (3" → 2") | 1 | 0.37 |
| 90° elbows | variable | 1.1 each |

The number of elbows is parameterized so it can be updated easily.

#### 5.2 Major losses (pipe friction)

Major losses are modeled using the Darcy–Weisbach equation:

$$ h_{major} = f \frac{L}{D} \frac{V^2}{2g} $$

Where:
- $L$ = total pipe length
- $D$ = pipe diameter
- $f$ = Darcy friction factor

The friction factor is computed using the Haaland equation:

$$ \frac{1}{\sqrt{f}} = -1.8 \log_{10} \left[ \left( \frac{\epsilon/D}{3.7} \right)^{1.11} + \frac{6.9}{Re} \right] $$

Pipe material is assumed to be PVC (very smooth), with roughness:
$$ \epsilon \approx 1.5 \times 10^{-6} \text{ m} $$

### 6. Pump Head Output

The final required pump head is:

$$ h_s = \Delta z + \frac{V_2^2}{2g} + h_{major} + h_{minor} $$

### 7. Pump Power Calculation

Hydraulic power added to the fluid:
$$ P_{hyd} = \rho g Q h_s $$

Pump shaft power (accounting for efficiency):
$$ P_{shaft} = \frac{P_{hyd}}{\eta} $$

Horsepower conversion:
$$ HP = \frac{P_{shaft}}{745.7} $$

### 8. Important Modeling Note (Exit Loss vs Outlet Velocity)

This model treats point 2 at the pipe outlet, so it explicitly includes:
$$ \frac{V_2^2}{2g} $$

Because of this, the model does **NOT** include a separate exit loss term of $K=1$.

If instead point 2 were chosen as a downstream reservoir free surface (where $V_2 \approx 0$), then an exit loss $K=1$ would be required.

### 9. Parameters You Can Easily Change

The code is designed so you can quickly update:
- Flow rate $Q$
- Elevation rise $\Delta z$
- Pipe length $L$
- Pipe diameter $D$
- Number of elbows
- Any fitting K values
- Pump efficiency $\eta$
