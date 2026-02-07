import sympy as sp

# Given
H = 0.2032 # m (8")
W = 0.1524 # m (6")
L = 3.6576 # m (12')
e = 1.5e-6 # m (absolute roughness for clear acrylic)
g = 9.81

rho = 998 # kg/m^3
mu  = 0.001 # Pa·s

# Hydraulic diameter for rectangular duct:
# Dh = 4A/P = 4(HW) / (2(H+W)) = 2HW/(H+W)
Dh = (2*H*W)/(H+W)

# Unknowns
v2, f, Re_D = sp.symbols('v2 f Re_D', positive=True)

# Bernoulli assumptions:
# P1 = P2 (atm) -> cancels
# v1 ~ 0 -> drops out
# z1 - z2 = v2^2/(2g) + h_major
z1 = 0.127   # m (5")
z2 = 0

h_major = f*(L/Dh)*(v2**2/(2*g))

eq1 = (z1 - z2) - (v2**2/(2*g)) - h_major
eq2 = Re_D - (rho*v2*Dh)/mu
eq3 = 1/sp.sqrt(f) + 1.8*sp.log(((e/Dh)/3.7)**1.11 + 6.9/Re_D, 10)

# Solve (guesses from non-loss results)
sol = sp.nsolve(
    (eq1, eq2, eq3),
    (v2, f, Re_D),
    (1.58, 0.014, 2.7e5)
)

v2_sol = sol[0]
f_sol  = sol[1]
Re_sol = sol[2]

# Flow rate (Q)
A = H*W
Q_m3_per_s = v2_sol*A

# Unit conversions
m_to_ft = 3.28084
m3_to_ft3 = 35.3147
m3s_to_gpm = 15850.3 # 1 m^3/s = 15850.3 gallons/min

v2_ft_s = v2_sol*m_to_ft
Q_ft3_s = Q_m3_per_s*m3_to_ft3
Q_gpm   = Q_m3_per_s*m3s_to_gpm

# Print results
print("==== Results ====")
print("v2 (m/s)   =", sp.N(v2_sol))
print("v2 (ft/s)  =", sp.N(v2_ft_s))
print()
print("f          =", sp.N(f_sol))
print("Re_D       =", sp.N(Re_sol))
print()
print("Q (m^3/s)  =", sp.N(Q_m3_per_s))
print("Q (ft^3/s) =", sp.N(Q_ft3_s))
print("Q (GPM)    =", sp.N(Q_gpm))