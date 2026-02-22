import math
import csv
import os
from datetime import datetime
from dataclasses import dataclass, field
from typing import List, Optional

# Unit helpers
FT_TO_M = 0.3048
IN_TO_M = 0.0254
HP_PER_WATT = 1.0 / 745.699872  # mechanical hp

def inch_diameter_to_m(d_in: float) -> float:
    return d_in * IN_TO_M

# Friction factor (Haaland)
def friction_factor_haaland(Re: float, rel_roughness: float) -> float:
    """
    Darcy friction factor.
    - Laminar: f = 64/Re
    - Turbulent: Haaland equation
    """
    if Re <= 0:
        raise ValueError("Re must be positive.")
    if Re < 2300:
        return 64.0 / Re

    # Haaland (valid for turbulent)
    term = (rel_roughness / 3.7)**1.11 + 6.9 / Re
    return 1.0 / ( (-1.8 * math.log10(term))**2 )

# Loss elements
@dataclass
class MinorLoss:
    name: str
    K: float
    diameter_m: Optional[float] = None  # if None, use system main diameter

@dataclass
class SystemParams:
    # Flow & geometry
    Q_m3_s: float = 0.006
    z1_m: float = 0.0
    z2_m: float = 3.0 * FT_TO_M

    # Main pipe (where most losses occur)
    D_main_m: float = inch_diameter_to_m(2.0)
    L_main_m: float = 15.0 * FT_TO_M

    # Fluid (water default ~20C)
    rho_kg_m3: float = 998.0
    mu_Pa_s: float = 1.002e-3
    g_m_s2: float = 9.80665

    # Pipe roughness (PVC ~ very smooth; allow override)
    eps_m: float = 1.5e-6  # ~0.0015 mm

    # Pump efficiency
    pump_efficiency: float = 0.65

    # Modeling choice:
    # If True: treat point 2 as reservoir free surface (V2=0) and add exit loss K=1
    # If False: treat point 2 at pipe outlet (V2=Q/A) and do NOT add exit loss
    point2_is_reservoir_free_surface: bool = False

    # Minor losses list
    minor_losses: List[MinorLoss] = field(default_factory=list)

def compute_velocity(Q: float, D: float) -> float:
    A = math.pi * (D**2) / 4.0
    return Q / A

def compute_reynolds(rho: float, V: float, D: float, mu: float) -> float:
    return rho * V * D / mu

def head_from_minor_losses(params: SystemParams, V_main: float) -> float:
    h_minor = 0.0
    for ml in params.minor_losses:
        D_use = ml.diameter_m if ml.diameter_m is not None else params.D_main_m
        V_use = compute_velocity(params.Q_m3_s, D_use)
        h_minor += ml.K * (V_use**2) / (2.0 * params.g_m_s2)
    return h_minor

def head_from_major_losses(params: SystemParams, V_main: float) -> float:
    Re = compute_reynolds(params.rho_kg_m3, V_main, params.D_main_m, params.mu_Pa_s)
    rel_rough = params.eps_m / params.D_main_m
    f = friction_factor_haaland(Re, rel_rough)
    h_major = f * (params.L_main_m / params.D_main_m) * (V_main**2) / (2.0 * params.g_m_s2)
    return h_major

def compute_pump_head_and_hp(params: SystemParams):
    # Velocity in main (2") line
    V_main = compute_velocity(params.Q_m3_s, params.D_main_m)

    # Elevation head
    delta_z = params.z2_m - params.z1_m

    # Kinetic term (depending on modeling choice)
    if params.point2_is_reservoir_free_surface:
        V2_term = 0.0  # free surface
        # add exit loss K=1 (jet dissipates)
        exit_loss = MinorLoss(name="Exit to reservoir", K=1.0, diameter_m=params.D_main_m)
        minor_losses = params.minor_losses + [exit_loss]
        temp_params = SystemParams(**{**params.__dict__, "minor_losses": minor_losses})
        h_minor = head_from_minor_losses(temp_params, V_main)
    else:
        # point 2 at pipe outlet -> keep V2^2/2g, no exit-loss K=1
        V2_term = (V_main**2) / (2.0 * params.g_m_s2)
        h_minor = head_from_minor_losses(params, V_main)

    h_major = head_from_major_losses(params, V_main)
    h_L = h_minor + h_major

    H_pump = delta_z + V2_term + h_L

    # Hydraulic power
    P_hyd_W = params.rho_kg_m3 * params.g_m_s2 * params.Q_m3_s * H_pump

    # Shaft power (account for efficiency)
    if not (0 < params.pump_efficiency <= 1.0):
        raise ValueError("pump_efficiency must be in (0, 1].")
    P_shaft_W = P_hyd_W / params.pump_efficiency
    P_shaft_hp = P_shaft_W * HP_PER_WATT

    return {
        "V_main_m_s": V_main,
        "delta_z_m": delta_z,
        "h_major_m": h_major,
        "h_minor_m": h_minor,
        "h_total_losses_m": h_L,
        "pump_head_m": H_pump,
        "hydraulic_power_W": P_hyd_W,
        "shaft_power_W": P_shaft_W,
        "shaft_power_hp": P_shaft_hp,
    }

if __name__ == "__main__":
    # Stated loss assumptions
    # Minor losses:
    # - Tee branch exiting weight tank: K = 1
    # - Contraction 3" -> 2": K = 0.37 (from online references)
    # - 6x 90-deg turns in 2" pipe: K = 1.1 each (from online references)
    n_elbows = 6

    params = SystemParams(
        Q_m3_s=0.006,
        z1_m = 0.0,
        z2_m = 5.24 * FT_TO_M,
        D_main_m = inch_diameter_to_m(3.0),
        L_main_m = 32.0 * FT_TO_M,
        eps_m = 1.5e-6,   # PVC
        pump_efficiency = 0.70,
        point2_is_reservoir_free_surface=False,  # "point 2 at outlet, has velocity" assumption
        minor_losses=[
            MinorLoss(name="Tee branch (exit weight tank)", K=1.0),
            MinorLoss(name=f"{n_elbows}x 90-deg elbows", K=1.1 * n_elbows),
            MinorLoss(name="Standard PVC Contraction 3in->1in((≈ 45° total angle)) ", K=0.4, diameter_m=inch_diameter_to_m(1.0)),
            MinorLoss(name="Sudden expansion (≈ 45° total angle) 1in->3in", K=0.79, diameter_m=inch_diameter_to_m(1.0)),
        ],
    )

    results = compute_pump_head_and_hp(params)

    print("---- Results ----")
    print(f"Main-line velocity V (3 in): {results['V_main_m_s']:.3f} m/s")
    print(f"Elevation head (z2-z1):     {results['delta_z_m']:.3f} m")
    print(f"Major losses:                {results['h_major_m']:.3f} m")
    print(f"Minor losses:                {results['h_minor_m']:.3f} m")
    print(f"Total losses:                {results['h_total_losses_m']:.3f} m")
    print(f"Required pump head H:        {results['pump_head_m']:.3f} m")
    print(f"Hydraulic power:             {results['hydraulic_power_W']:.1f} W")
    print(f"Shaft power (@eta):          {results['shaft_power_W']:.1f} W")
    print(f"Shaft power (@eta):          {results['shaft_power_hp']:.3f} hp")

    # Save results to CSV

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_path = os.path.join(os.path.dirname(__file__), f"pump_hp_results_{timestamp}.csv")
    rows = [
        ("Parameter", "Value", "Unit"),
        ("Flow rate (Q)",            params.Q_m3_s,                      "m³/s"),
        ("Main pipe diameter",       params.D_main_m,                    "m"),
        ("Pipe length",              params.L_main_m,                    "m"),
        ("Pipe roughness (eps)",     params.eps_m,                       "m"),
        ("Elevation difference",     results["delta_z_m"],               "m"),
        ("Main-line velocity",       results["V_main_m_s"],              "m/s"),
        ("Major losses",             results["h_major_m"],               "m"),
        ("Minor losses",             results["h_minor_m"],               "m"),
        ("Total losses",             results["h_total_losses_m"],        "m"),
        ("Required pump head",       results["pump_head_m"],             "m"),
        ("Hydraulic power",          results["hydraulic_power_W"],       "W"),
        ("Shaft power",              results["shaft_power_W"],           "W"),
        ("Shaft power",              results["shaft_power_hp"],          "hp"),
        ("Pump efficiency",          params.pump_efficiency,             "-"),
    ]
    with open(csv_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerows(rows)
    print(f"\nResults saved to: {csv_path}")
