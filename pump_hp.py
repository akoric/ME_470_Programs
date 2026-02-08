"""
Solve for required pump head (h_s) from:

z1 + v1^2/(2g) + h_s = h_L      =>      h_s = h_L - z1 - v1^2/(2g)

where h_L = (minor losses) + (major losses)

Major losses use Darcy–Weisbach with Haaland friction factor.
All geometry / K-values are parameterized so you can plug in your exact setup.

Also prints required pump power from h_s:
    Hydraulic power: P_h = rho * g * Q * h_s   [W]
    Horsepower:      HP  = P_h / 745.699872    [hp]
Optionally includes pump efficiency if you set eta_pump.

Compatible with Python 3.13+ (fixes dataclass default_factory issue).
"""

from dataclasses import dataclass, field
from math import pi, log10

# -----------------------
# Constants / conversions
# -----------------------
g = 9.80665                 # m/s^2
FT_TO_M = 0.3048
IN_TO_M = 0.0254
W_PER_HP = 745.699872       # mechanical horsepower (US)


# -----------------------
# Helpers
# -----------------------
def area(D_m: float) -> float:
    return pi * (D_m ** 2) / 4.0


def velocity(Q_m3s: float, D_m: float) -> float:
    return Q_m3s / area(D_m)


def reynolds(rho: float, mu: float, V: float, D: float) -> float:
    return rho * V * D / mu


def f_haaland(Re: float, eps: float, D: float) -> float:
    """
    Haaland equation (Darcy friction factor), valid for turbulent flow.
    For laminar (Re < 2300), switches to f = 64/Re.
    """
    if Re <= 0:
        raise ValueError("Reynolds number must be positive.")
    if Re < 2300:
        return 64.0 / Re

    term = ((eps / D) / 3.7) ** 1.11 + 6.9 / Re
    return 1.0 / ((-1.8 * log10(term)) ** 2)


def head_loss_minor(K: float, V: float) -> float:
    return K * (V ** 2) / (2.0 * g)


def head_loss_major(f: float, L: float, D: float, V: float) -> float:
    return f * (L / D) * (V ** 2) / (2.0 * g)


def pump_power_from_head(rho: float, Q: float, hs: float, eta_pump: float = 1.0) -> dict:
    """
    Returns hydraulic power and shaft power (if eta_pump < 1).
    eta_pump = pump efficiency (0 < eta <= 1). If you don't know it, leave as 1.0.
    """
    if eta_pump <= 0 or eta_pump > 1:
        raise ValueError("eta_pump must be in (0, 1].")

    P_h_W = rho * g * Q * hs                     # hydraulic power added to fluid [W]
    P_shaft_W = P_h_W / eta_pump                 # shaft power required [W]
    return {
        "P_h_W": P_h_W,
        "P_h_hp": P_h_W / W_PER_HP,
        "P_shaft_W": P_shaft_W,
        "P_shaft_hp": P_shaft_W / W_PER_HP,
        "eta_pump": eta_pump,
    }


# -----------------------
# Model parameters
# -----------------------
@dataclass
class Fluid:
    rho: float = 998.0        # kg/m^3 (water ~20C)
    mu: float = 1.002e-3      # Pa*s  (water ~20C)


@dataclass
class PipeSegment:
    D_m: float               # diameter (m)
    L_m: float               # length (m)
    eps_m: float = 1.5e-6     # roughness (m) default = PVC

    def major_loss(self, Q: float, fluid: Fluid) -> float:
        V = velocity(Q, self.D_m)
        Re = reynolds(fluid.rho, fluid.mu, V, self.D_m)
        f = f_haaland(Re, self.eps_m, self.D_m)
        return head_loss_major(f, self.L_m, self.D_m, V)


@dataclass
class LossModel:
    # Flow
    Q_m3s: float = 0.006

    # Elevation at point 1 (ft -> m)
    z1_ft: float = 3.0

    # Diameters
    D_exit_in: float = 2.0     # where v1 is evaluated (exit / 2-in pipe)

    # Minor losses (K values)
    K_tee_branch: float = 1.0      # given
    K_contraction: float = 0.4     # placeholder (set yours)
    K_elbow_90: float = 0.9        # placeholder (set yours)
    n_elbows: int = 6

    # Optional extra minor losses (set to 0 if not used)
    K_entrance: float = 0.0
    K_exit: float = 0.0

    # Where each minor loss “sees” the velocity
    D_tee_in: float = 3.0
    D_contraction_out_in: float = 2.0

    # Major-loss pipe segment (“x length” of 2-in pipe)
    L_major_m: float = 10.0
    eps_major_m: float = 1.5e-6     # PVC default

    # Pump efficiency (set to something like 0.6–0.8 if you want shaft power)
    eta_pump: float = 1.0

    # Fluid props (FIXED: use default_factory)
    fluid: Fluid = field(default_factory=Fluid)

    def solve(self) -> dict:
        Q = self.Q_m3s
        z1_m = self.z1_ft * FT_TO_M

        # v1 based on exit area (2-in pipe by default)
        D_exit_m = self.D_exit_in * IN_TO_M
        v1 = velocity(Q, D_exit_m)

        # Velocities for minor-loss elements
        V_tee = velocity(Q, self.D_tee_in * IN_TO_M)
        V_2in = velocity(Q, self.D_contraction_out_in * IN_TO_M)

        # Minor losses
        h_minor = 0.0
        h_minor += head_loss_minor(self.K_tee_branch, V_tee)
        h_minor += head_loss_minor(self.K_contraction, V_2in)
        h_minor += head_loss_minor(self.n_elbows * self.K_elbow_90, V_2in)
        h_minor += head_loss_minor(self.K_entrance, V_2in)
        h_minor += head_loss_minor(self.K_exit, V_2in)

        # Major losses (2-in pipe segment)
        seg = PipeSegment(
            D_m=2.0 * IN_TO_M,
            L_m=self.L_major_m,
            eps_m=self.eps_major_m
        )
        h_major = seg.major_loss(Q, self.fluid)

        hL = h_minor + h_major

        # From your stated Bernoulli form:
        # z1 + v1^2/(2g) + h_s = h_L
        hs = hL - z1_m - (v1 ** 2) / (2.0 * g)

        # Power from head
        pwr = pump_power_from_head(self.fluid.rho, Q, hs, self.eta_pump)

        return {
            "Q_m3s": Q,
            "z1_m": z1_m,
            "D_exit_m": D_exit_m,
            "v1_mps": v1,
            "h_minor_m": h_minor,
            "h_major_m": h_major,
            "hL_total_m": hL,
            "h_s_m": hs,
            # power
            "P_h_W": pwr["P_h_W"],
            "P_h_hp": pwr["P_h_hp"],
            "P_shaft_W": pwr["P_shaft_W"],
            "P_shaft_hp": pwr["P_shaft_hp"],
            "eta_pump": pwr["eta_pump"],
        }


# -----------------------
# Example usage
# -----------------------
if __name__ == "__main__":
    model = LossModel(
        Q_m3s=0.006,
        z1_ft=3.0,

        # Put your real fitting loss coefficients here:
        K_contraction=0.37,
        K_elbow_90=1.1,
        n_elbows=6,

        # Your x length of 2-in PVC pipe:
        L_major_m=4.5,

        # PVC roughness default already, but you can override:
        eps_major_m=1.5e-6,

        # Entrance/exit losses if desired:
        K_entrance=0.0,
        K_exit=0.0,

        # Pump efficiency (1.0 prints hydraulic HP; e.g. 0.7 prints shaft HP too)
        eta_pump=0.70,
    )

    out = model.solve()

    # Pretty print key results
    print("\n--- Results ---")
    print(f"Q               : {out['Q_m3s']:.6g} m^3/s")
    print(f"z1              : {out['z1_m']:.6g} m")
    print(f"v1              : {out['v1_mps']:.6g} m/s")
    print(f"h_minor         : {out['h_minor_m']:.6g} m")
    print(f"h_major         : {out['h_major_m']:.6g} m")
    print(f"h_L (total)     : {out['hL_total_m']:.6g} m")
    print(f"h_s (pump head) : {out['h_s_m']:.6g} m")

    print("\n--- Power ---")
    print(f"Hydraulic power : {out['P_h_W']:.6g} W  ({out['P_h_hp']:.6g} hp)")
    print(f"Pump efficiency : {out['eta_pump']:.6g}")
    print(f"Shaft power     : {out['P_shaft_W']:.6g} W  ({out['P_shaft_hp']:.6g} hp)\n")