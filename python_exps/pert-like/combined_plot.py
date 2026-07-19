"""
Overlay: Exact Numerical Convolution vs Monte Carlo Simulation
------------------------------------------------------------------
Runs both methods and plots their CDFs on the same graph to visually
confirm they match.
"""

import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import beta as beta_dist
from scipy.integrate import cumulative_trapezoid, trapezoid

# =========================================================
# PART A: Exact numerical convolution (deterministic)
# =========================================================
def pert_params(o, m, p):
    alpha = 1 + 4 * (m - o) / (p - o)
    beta_ = 1 + 4 * (p - m) / (p - o)
    return alpha, beta_, o, p - o

specs = {
    "A": (2, 4, 12),
    "B": (10, 12, 26),
    "C": (8, 9, 10),
    "D": (10, 15, 20),
    "E": (7, 7.5, 11),
    "G": (3, 3.5, 7),
}
rv = {act: beta_dist(*pert_params(*spec)[:2], loc=pert_params(*spec)[2], scale=pert_params(*spec)[3])
      for act, spec in specs.items()}

dx = 0.01
d_grid = np.arange(10, 20 + dx, dx)
g_grid = np.arange(3, 7 + dx, dx)
pdf_D = rv["D"].pdf(d_grid)
pdf_G = rv["G"].pdf(g_grid)
pdf_DG = np.convolve(pdf_D, pdf_G) * dx
dg_grid = np.arange(d_grid[0] + g_grid[0], d_grid[0] + g_grid[0] + len(pdf_DG) * dx - dx/2, dx)[:len(pdf_DG)]
cdf_DG_vals = np.clip(cumulative_trapezoid(pdf_DG, dx=dx, initial=0), 0, 1)
def cdf_DG(y):
    return np.interp(y, dg_grid, cdf_DG_vals, left=0.0, right=1.0)

a_grid = np.arange(2, 12 + dx, dx)
pdf_A_vals = rv["A"].pdf(a_grid)
x_grid = np.arange(10, 55, 0.02)
F_exact = np.zeros_like(x_grid)
for i, x in enumerate(x_grid):
    cdf_C_vals = rv["C"].cdf(x - a_grid - 14)
    cdf_DG_here = cdf_DG(x - a_grid - 5)
    cdf_E_vals = rv["E"].cdf(x - a_grid - 5)
    integrand = pdf_A_vals * cdf_C_vals * cdf_DG_here * cdf_E_vals
    inner = trapezoid(integrand, a_grid)
    F_exact[i] = inner * rv["B"].cdf(x - 14)
F_exact = np.clip(F_exact, 0, 1)

pdf_x = np.clip(np.gradient(F_exact, x_grid), 0, None)
mean_exact = trapezoid(x_grid * pdf_x, x_grid)
var_exact = trapezoid((x_grid - mean_exact) ** 2 * pdf_x, x_grid)
std_exact = np.sqrt(var_exact)

def prob_within_exact(x_target):
    return np.interp(x_target, x_grid, F_exact) * 100

# =========================================================
# PART B: Monte Carlo simulation (full network, all 8 activities)
# =========================================================
activities = {
    "A": (2, 4, 12), "B": (10, 12, 26), "C": (8, 9, 10), "D": (10, 15, 20),
    "E": (7, 7.5, 11), "F": (9, 9, 9), "G": (3, 3.5, 7), "H": (5, 5, 5),
}
N = 20_000_000
rng = np.random.default_rng(42)

def sample_beta_pert(o, m, p, size, rng):
    if p == o:
        return np.full(size, m)
    lam = 4
    alpha = 1 + lam * (m - o) / (p - o)
    beta_ = 1 + lam * (p - m) / (p - o)
    s = rng.beta(alpha, beta_, size)
    return o + s * (p - o)

dur = {act: sample_beta_pert(o, m, p, N, rng) for act, (o, m, p) in activities.items()}
path_ACFH = dur["A"] + dur["C"] + dur["F"] + dur["H"]
path_BFH  = dur["B"] + dur["F"] + dur["H"]
path_ADGH = dur["A"] + dur["D"] + dur["G"] + dur["H"]
path_AEH  = dur["A"] + dur["E"] + dur["H"]
project_time = np.maximum.reduce([path_ACFH, path_BFH, path_ADGH, path_AEH])

mean_mc = project_time.mean()
std_mc = project_time.std()

# Empirical CDF on the same x_grid (for direct overlay)
sorted_pt = np.sort(project_time)
F_mc_on_grid = np.searchsorted(sorted_pt, x_grid, side="right") / N

def prob_within_mc(x_target):
    return np.mean(project_time <= x_target) * 100

# =========================================================
# PART C: Print results
# =========================================================
CP, BEFORE, BEYOND = 29, 22, 36
print("=" * 70)
print(f"{'Method':30s}{'Mean':>8s}{'Std':>8s}{'P(<=22)':>10s}{'P(<=29)':>10s}{'P(<=36)':>10s}")
print(f"{'Exact numerical convolution':30s}{mean_exact:8.3f}{std_exact:8.3f}"
      f"{prob_within_exact(BEFORE):10.3f}{prob_within_exact(CP):10.3f}{prob_within_exact(BEYOND):10.3f}")
print(f"{'Monte Carlo (20,000,000 trials)':30s}{mean_mc:8.3f}{std_mc:8.3f}"
      f"{prob_within_mc(BEFORE):10.3f}{prob_within_mc(CP):10.3f}{prob_within_mc(BEYOND):10.3f}")
print("=" * 70)

# =========================================================
# PART D: Overlay plot
# =========================================================
fig, ax = plt.subplots(figsize=(10, 6))

ax.plot(x_grid, F_mc_on_grid * 100, color="#3ec9b0", linewidth=3.5,
        alpha=0.55, label="Monte Carlo (20M trials)")
ax.plot(x_grid, F_exact * 100, color="#e8a33d", linewidth=1.8, linestyle="--",
        label="Exact numerical convolution")

for x_val, label in [(BEFORE, "-7 days"), (CP, "Critical Path"), (BEYOND, "+7 days")]:
    y_val = prob_within_exact(x_val)
    ax.scatter([x_val], [y_val], color="#e5654a", zorder=5, s=35)
    ax.annotate(f"{label}\n({x_val}d, {y_val:.1f}%)",
                xy=(x_val, y_val), xytext=(x_val + 1, y_val - 10),
                fontsize=9, color="#e5654a")

ax.axhline(50, color="gray", linestyle=":", linewidth=0.8)
ax.set_xlabel("Project Duration (days)")
ax.set_ylabel("Cumulative Probability (%)")
ax.set_title("Project Completion Probability: Exact Analytical vs Monte Carlo")
ax.set_xlim(mean_mc - 4.5 * std_mc, mean_mc + 4.5 * std_mc)
ax.set_ylim(0, 100)
ax.grid(alpha=0.3)
ax.legend(loc="lower right")

plt.tight_layout()
plt.savefig("./overlay_comparison.png", dpi=150)
print("Saved plot to overlay_comparison.png")
