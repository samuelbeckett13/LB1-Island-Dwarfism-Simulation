"""
LB1 DEVELOPMENTAL PHYSIOLOGY MODEL — VERSION 13 FINAL
FROZEN THESIS MODEL: FLORES BASELINE + DEVELOPMENTAL PERTURBATION + ROBUSTNESS

CORE CHANGE
-----------
Previous versions effectively asked whether developmental/endocrine disruption
could transform an average modern-human reference phenotype into LB1.

Version 12 separates two levels of biology:

    LEVEL 1: long-term Flores small-body adaptation
        modern-sized ancestral reference
            -> small-bodied Flores population baseline

    LEVEL 2: individual developmental perturbation
        Flores baseline
            -> IGF / iodine-thyroid / maternal-environment effects
            -> LB1-like phenotype?

This prevents the developmental model from being forced to explain a
population-level small-body phenotype that fossil evidence indicates was
already established on Flores by ~700 ka.

IMPORTANT SCIENTIFIC LIMITATION
-------------------------------
The Flores fossil record is too sparse to estimate a true population mean and
standard deviation for femur, tibia, humerus, foot, or ICV at Liang Bua.

Therefore Version 12 does NOT invent a precise "Flores population mean."
Instead it uses a broad fossil-constrained BODY-SCALE SENSITIVITY PRIOR and
reports results across that uncertainty.

The prior is NOT an empirical population distribution.

FOSSIL BASIS FOR SMALL-BODY BASELINE
------------------------------------
Kaifu et al. 2024:
- Mata Menge adult humerus estimated 211–220 mm.
- It is 9–16% shorter than LB1.
- Humerus-based stature estimates:
      Mata Menge: 103–108 cm
      LB1:        121 cm
  using a human pygmy model.
- Authors conclude markedly diminutive body size existed on Flores by
  at least ~700,000 years ago and remained broadly stable over the lineage.

This justifies treating "small-bodied Flores" as a population-level baseline
condition, but does NOT provide enough data to estimate its exact distribution.

MODEL DESIGN
------------
We therefore sample:
    FLORES_LINEAR_SCALE ~ Uniform(0.64, 0.80)

This is deliberately broad and labeled a SENSITIVITY PRIOR.
It represents the plausible magnitude of long-bone/stature reduction relative
to the modern female reference used in Versions 9–11.

For brain size, population-level body-size adaptation is allowed to alter ICV
through uncertain allometry:
    baseline_ICV = modern_ICV * linear_scale ^ brain_linear_exponent

where:
    brain_linear_exponent ~ Uniform(1.6, 2.2)

This brackets a roughly quadratic linear-size relationship while acknowledging
that hominin brain-body allometry is not a simple fixed power law.

Crucially, the code also runs a BODY-ONLY Flores baseline in which ICV is not
allometrically reduced. This reveals how strongly conclusions depend on the
brain-allometry assumption.

SCORING ENDPOINTS
-----------------
1. Femur length                280 mm
2. ICV                         430 cc
3. Crural index                83.9
4. Humerofemoral index         87.8
5. Foot/femur index            70.0

This remains a physiological-compatibility / sensitivity model, not a claim
about historical causation, diagnosis, ancestry, or taxonomy.
"""

import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

SEED = int(os.getenv("LB1_SEED", "20260813"))
N = int(os.getenv("LB1_N_SIMULATIONS", "500000"))
rng = np.random.default_rng(SEED)
BASE = os.path.dirname(os.path.abspath(__file__))

# ============================================================
# 1. LB1 TARGET VECTOR
# ============================================================

LB1 = {
    "femur": 280.0,
    "icv": 430.0,
    "crural_index": 83.9,
    "humerofemoral_index": 87.8,
    "foot_femur_index": 70.0
}

# Context-only absolute lengths.
LB1_CONTEXT = {
    "tibia": 235.0,
    "humerus": 243.0,
    "foot": 196.0
}

# ============================================================
# 2. MODERN FEMALE REFERENCE — BENCHMARK ONLY
# ============================================================

REF = {
    "femur_mean": 434.0,
    "femur_sd": 24.0,
    "icv_mean": 1341.0,
    "icv_sd": 100.0,
    "crural_mean": 83.5,
    "crural_sd": 2.3,
    "humerofemoral_mean": 71.5,
    "humerofemoral_sd": 2.3,
    "foot_femur_mean": 54.2,
    "foot_femur_sd": 2.5
}

REF_TIBIA = REF["femur_mean"] * REF["crural_mean"] / 100.0
REF_HUMERUS = REF["femur_mean"] * REF["humerofemoral_mean"] / 100.0
REF_FOOT = REF["femur_mean"] * REF["foot_femur_mean"] / 100.0

# ============================================================
# 3. FLORES POPULATION-BASELINE SENSITIVITY PRIORS
# ============================================================

FLORES_LINEAR_SCALE_BOUNDS = (0.64, 0.80)

# Brain volume vs linear body-size scaling sensitivity.
# NOT a measured H. floresiensis exponent.
FLORES_BRAIN_LINEAR_EXPONENT_BOUNDS = (1.6, 2.2)

# Small amount of baseline ratio variability.
# These are intentionally modest because the fossil record is too sparse
# to estimate population distributions.
BASELINE_CRURAL_SHIFT_SD = 1.5
BASELINE_HFI_SHIFT_SD = 2.0
BASELINE_FFI_SHIFT_SD = 2.0

# ============================================================
# 4. PRENATAL GROWTH TRAJECTORIES
# ============================================================

BONE_WEEKS = np.arange(14, 41, dtype=float)

FEMUR_VALUES = np.array([
    13.1,16.3,19.5,22.5,25.5,28.5,31.3,34.1,36.7,
    39.4,41.9,44.4,46.7,49.0,51.3,53.4,55.5,57.5,
    59.4,61.3,63.1,64.8,66.4,67.9,69.4,70.8,72.1
])

BRAIN_WEEKS = np.array([
    20.5,22.5,24.5,26.5,28.5,30.5,32.5,34.5
])

BRAIN_VALUES = np.array([
    71.2,99.8,139.5,169.1,217.0,269.9,306.0,366.3
])

def make_cdf(weeks, values, step=0.05):
    grid = np.arange(weeks.min(), weeks.max() + step/2, step)
    y = np.interp(grid, weeks, values)
    velocity = np.clip(np.gradient(y, grid), 0, None)
    density = velocity / np.trapezoid(velocity, grid)

    increments = 0.5 * (density[:-1] + density[1:]) * np.diff(grid)
    cdf = np.r_[0.0, np.cumsum(increments)]
    cdf /= cdf[-1]

    return grid, cdf

BONE_GRID, BONE_CDF = make_cdf(BONE_WEEKS, FEMUR_VALUES)
BRAIN_GRID, BRAIN_CDF = make_cdf(BRAIN_WEEKS, BRAIN_VALUES)

def overlap_fraction(grid, cdf, start, duration):
    end = start + duration
    a = np.interp(start, grid, cdf, left=0.0, right=1.0)
    b = np.interp(end, grid, cdf, left=0.0, right=1.0)
    return np.clip(b - a, 0.0, 1.0)

def early_neural_fraction(start, duration):
    end = start + duration
    overlap = np.maximum(
        0.0,
        np.minimum(end, 20.0) - np.maximum(start, 4.0)
    )
    return np.clip(overlap / 16.0, 0.0, 1.0)

# ============================================================
# 5. SCORING
# ============================================================

def phenotype_score(femur, icv, tibia, humerus, foot):
    crural = 100.0 * tibia / femur
    hfi = 100.0 * humerus / femur
    ffi = 100.0 * foot / femur

    comps = {
        "femur_component":
            ((femur - LB1["femur"]) / REF["femur_sd"]) ** 2,

        "icv_component":
            ((icv - LB1["icv"]) / REF["icv_sd"]) ** 2,

        "crural_component":
            ((crural - LB1["crural_index"]) / REF["crural_sd"]) ** 2,

        "humerofemoral_component":
            ((hfi - LB1["humerofemoral_index"]) /
             REF["humerofemoral_sd"]) ** 2,

        "foot_femur_component":
            ((ffi - LB1["foot_femur_index"]) /
             REF["foot_femur_sd"]) ** 2,
    }

    total = sum(comps.values())

    return total, crural, hfi, ffi, comps

def U(lo, hi, n):
    return rng.uniform(lo, hi, n)

# ============================================================
# 6. POPULATION BASELINES
# ============================================================

def modern_baseline(n):
    return {
        "baseline_type": np.array(["Modern benchmark"] * n),
        "linear_scale": np.ones(n),
        "brain_exponent": np.zeros(n),
        "femur": np.full(n, REF["femur_mean"]),
        "tibia": np.full(n, REF_TIBIA),
        "humerus": np.full(n, REF_HUMERUS),
        "foot": np.full(n, REF_FOOT),
        "icv": np.full(n, REF["icv_mean"])
    }

def flores_baseline(n, allometric_brain=True):
    """
    Fossil-constrained sensitivity baseline.

    Scale is NOT an estimated population distribution.
    """
    scale = U(
        FLORES_LINEAR_SCALE_BOUNDS[0],
        FLORES_LINEAR_SCALE_BOUNDS[1],
        n
    )

    # Baseline limb indices are allowed modest uncertainty.
    crural = np.clip(
        rng.normal(
            REF["crural_mean"],
            BASELINE_CRURAL_SHIFT_SD,
            n
        ),
        77, 90
    )

    hfi = np.clip(
        rng.normal(
            REF["humerofemoral_mean"],
            BASELINE_HFI_SHIFT_SD,
            n
        ),
        64, 82
    )

    ffi = np.clip(
        rng.normal(
            REF["foot_femur_mean"],
            BASELINE_FFI_SHIFT_SD,
            n
        ),
        47, 63
    )

    femur = REF["femur_mean"] * scale
    tibia = femur * crural / 100.0
    humerus = femur * hfi / 100.0
    foot = femur * ffi / 100.0

    if allometric_brain:
        exponent = U(
            FLORES_BRAIN_LINEAR_EXPONENT_BOUNDS[0],
            FLORES_BRAIN_LINEAR_EXPONENT_BOUNDS[1],
            n
        )
        icv = REF["icv_mean"] * np.power(scale, exponent)
        name = "Flores small-body + brain allometry"
    else:
        exponent = np.zeros(n)
        icv = np.full(n, REF["icv_mean"])
        name = "Flores small-body only"

    return {
        "baseline_type": np.array([name] * n),
        "linear_scale": scale,
        "brain_exponent": exponent,
        "femur": femur,
        "tibia": tibia,
        "humerus": humerus,
        "foot": foot,
        "icv": icv
    }

# ============================================================
# 7. DEVELOPMENTAL PATHWAYS
# ============================================================

def igf_losses(n):
    start = U(14, 30, n)
    duration = U(4, 14, n)
    severity = U(.20, 1.00, n)

    bf = overlap_fraction(
        BONE_GRID, BONE_CDF, start, duration
    )
    cf = overlap_fraction(
        BRAIN_GRID, BRAIN_CDF, start, duration
    )

    bc = U(.55, 1.00, n)
    cc = bc * U(.25, .75, n)

    bone = (
        severity * bc * bf * U(.60, 1.00, n)
    )

    brain = (
        severity * cc * cf * U(.45, .90, n)
    )

    return np.clip(bone, 0, .95), np.clip(brain, 0, .95)

def iodine_losses(n):
    iodine = U(0, 1, n)
    thyroid = iodine * U(.25, 1.00, n)

    start = U(4, 24, n)
    duration = U(2, 24, n)

    early = early_neural_fraction(start, duration)
    late = overlap_fraction(
        BRAIN_GRID, BRAIN_CDF, start, duration
    )
    bf = overlap_fraction(
        BONE_GRID, BONE_CDF, start, duration
    )

    brain_timing = np.clip(.70 * early + .30 * late, 0, 1)

    bone = (
        thyroid *
        U(0, .35, n) *
        bf *
        U(.10, .70, n)
    )

    brain = (
        thyroid *
        U(.30, 1.00, n) *
        brain_timing *
        U(.60, 1.00, n)
    )

    return (
        np.clip(bone, 0, .95),
        np.clip(brain, 0, .95),
        iodine
    )

def multigenerational_susceptibility(n):
    """
    Recurrent environmental state with regression toward baseline.

    Does NOT directly reduce anatomy.
    """
    generations = rng.integers(2, 7, n)
    chronic_burden = U(0, 1, n)
    rho = U(.05, .50, n)
    coupling = U(.05, .30, n)

    state = np.zeros(n)

    for g in range(6):
        active = generations > g

        shock = np.clip(
            chronic_burden + rng.normal(0, .12, n),
            0, 1
        )

        proposal = (
            rho * state +
            coupling * shock * (1 - state)
        )

        state = np.where(
            active,
            np.clip(proposal, 0, 1),
            state
        )

    gain = U(0, .50, n)
    susceptibility = np.clip(
        1 + gain * state,
        1, 1.5
    )

    return generations, chronic_burden, state, susceptibility

# ============================================================
# 8. SEGMENT-SPECIFIC DEVELOPMENTAL RESPONSE
# ============================================================

def apply_segment_response(
    baseline,
    total_femur_loss,
    iodine_fraction,
    n
):
    # Same constrained response architecture as V11.
    tibia_multiplier = U(.88, 1.08, n)
    humerus_multiplier = U(.62, .92, n)
    foot_multiplier = U(.45, .80, n)

    humerus_multiplier *= (1 - .08 * iodine_fraction)
    foot_multiplier *= (1 - .08 * iodine_fraction)

    tibia_loss = np.clip(
        total_femur_loss * tibia_multiplier,
        0, .95
    )

    humerus_loss = np.clip(
        total_femur_loss * humerus_multiplier,
        0, .95
    )

    foot_loss = np.clip(
        total_femur_loss * foot_multiplier,
        0, .95
    )

    return {
        "femur": baseline["femur"] * (1 - total_femur_loss),
        "tibia": baseline["tibia"] * (1 - tibia_loss),
        "humerus": baseline["humerus"] * (1 - humerus_loss),
        "foot": baseline["foot"] * (1 - foot_loss),
    }

# ============================================================
# 9. SIMULATE ONE ARCHITECTURE
# ============================================================

def simulate(
    name,
    baseline_mode,
    use_igf,
    use_iodine,
    use_multigen,
    n=N
):
    if baseline_mode == "modern":
        baseline = modern_baseline(n)

    elif baseline_mode == "flores_body_only":
        baseline = flores_baseline(
            n,
            allometric_brain=False
        )

    elif baseline_mode == "flores_allometric":
        baseline = flores_baseline(
            n,
            allometric_brain=True
        )

    else:
        raise ValueError("Unknown baseline mode.")

    igf_bone = np.zeros(n)
    igf_brain = np.zeros(n)

    iodine_bone = np.zeros(n)
    iodine_brain = np.zeros(n)
    iodine_burden = np.zeros(n)

    if use_igf:
        igf_bone, igf_brain = igf_losses(n)

    if use_iodine:
        iodine_bone, iodine_brain, iodine_burden = (
            iodine_losses(n)
        )

    if use_multigen:
        generations, env, mg_state, susceptibility = (
            multigenerational_susceptibility(n)
        )
    else:
        generations = np.ones(n, dtype=int)
        env = np.zeros(n)
        mg_state = np.zeros(n)
        susceptibility = np.ones(n)

    igf_bone = np.clip(
        igf_bone * susceptibility,
        0, .95
    )
    igf_brain = np.clip(
        igf_brain * susceptibility,
        0, .95
    )

    iodine_bone = np.clip(
        iodine_bone * susceptibility,
        0, .95
    )
    iodine_brain = np.clip(
        iodine_brain * susceptibility,
        0, .95
    )

    total_bone_loss = 1 - (
        (1 - igf_bone) *
        (1 - iodine_bone)
    )

    total_brain_loss = 1 - (
        (1 - igf_brain) *
        (1 - iodine_brain)
    )

    total_bone_loss = np.clip(
        total_bone_loss, 0, .95
    )
    total_brain_loss = np.clip(
        total_brain_loss, 0, .95
    )

    iodine_fraction = (
        iodine_bone /
        np.maximum(total_bone_loss, 1e-12)
    )
    iodine_fraction = np.clip(
        iodine_fraction, 0, 1
    )

    limbs = apply_segment_response(
        baseline,
        total_bone_loss,
        iodine_fraction,
        n
    )

    icv = baseline["icv"] * (
        1 - total_brain_loss
    )

    score, crural, hfi, ffi, comps = phenotype_score(
        limbs["femur"],
        icv,
        limbs["tibia"],
        limbs["humerus"],
        limbs["foot"]
    )

    return pd.DataFrame({
        "model": name,
        "baseline_type": baseline["baseline_type"],
        "baseline_linear_scale": baseline["linear_scale"],
        "baseline_brain_exponent": baseline["brain_exponent"],

        "baseline_femur": baseline["femur"],
        "baseline_tibia": baseline["tibia"],
        "baseline_humerus": baseline["humerus"],
        "baseline_foot": baseline["foot"],
        "baseline_icv": baseline["icv"],

        "use_igf": use_igf,
        "use_iodine": use_iodine,
        "use_multigen": use_multigen,

        "generations": generations,
        "environmental_burden": env,
        "multigenerational_state": mg_state,
        "susceptibility": susceptibility,
        "iodine_burden": iodine_burden,

        "developmental_femur_loss": total_bone_loss,
        "developmental_brain_loss": total_brain_loss,

        "femur": limbs["femur"],
        "tibia": limbs["tibia"],
        "humerus": limbs["humerus"],
        "foot": limbs["foot"],
        "icv": icv,

        "crural_index": crural,
        "humerofemoral_index": hfi,
        "foot_femur_index": ffi,

        "distance": score,
        **comps
    })

# ============================================================
# 10. EXPERIMENTS
# ============================================================

EXPERIMENTS = [
    # Old conceptual benchmark.
    (
        "Modern baseline + full developmental model",
        "modern",
        True, True, True
    ),

    # What small-body adaptation alone does.
    (
        "Flores body-only baseline; no developmental insult",
        "flores_body_only",
        False, False, False
    ),

    # Separates effect of assuming body-brain allometry.
    (
        "Flores allometric baseline; no developmental insult",
        "flores_allometric",
        False, False, False
    ),

    (
        "Flores baseline + IGF",
        "flores_allometric",
        True, False, False
    ),

    (
        "Flores baseline + iodine",
        "flores_allometric",
        False, True, False
    ),

    (
        "Flores baseline + IGF + iodine",
        "flores_allometric",
        True, True, False
    ),

    (
        "Flores baseline + full developmental model",
        "flores_allometric",
        True, True, True
    )
]

def summarize(df):
    best = df.loc[df["distance"].idxmin()]

    return {
        "Model": best["model"],
        "Simulations": len(df),

        "Best Distance": best["distance"],
        "Median Distance": df["distance"].median(),

        "Baseline Scale": best["baseline_linear_scale"],
        "Baseline ICV": best["baseline_icv"],

        "Best Femur": best["femur"],
        "Best Tibia": best["tibia"],
        "Best Humerus": best["humerus"],
        "Best Foot": best["foot"],
        "Best ICV": best["icv"],

        "Best Crural Index": best["crural_index"],
        "Best Humerofemoral Index":
            best["humerofemoral_index"],
        "Best Foot/Femur Index":
            best["foot_femur_index"],

        "P(D<5)": (df["distance"] < 5).mean(),
        "P(D<10)": (df["distance"] < 10).mean(),
        "P(D<20)": (df["distance"] < 20).mean(),
        "P(D<40)": (df["distance"] < 40).mean(),
    }

print("=" * 92)
print("LB1 DEVELOPMENTAL PHYSIOLOGY MODEL — VERSION 12")
print("FLORES POPULATION BASELINE + INDIVIDUAL DEVELOPMENTAL PERTURBATION")
print("=" * 92)
print("Simulations per experiment:", f"{N:,}")
print()

runs = {}
rows = []

for exp in EXPERIMENTS:
    name, mode, igf, iodine, mg = exp
    print("Running:", name)

    df = simulate(
        name,
        mode,
        igf,
        iodine,
        mg,
        N
    )

    runs[name] = df
    rows.append(summarize(df))

summary = pd.DataFrame(
    rows
).sort_values("Best Distance")

print()
print("=" * 92)
print("VERSION 12 MODEL COMPARISON")
print("=" * 92)
print(summary.to_string(index=False))

# ============================================================
# 11. BEST FULL FLORES MODEL
# ============================================================

full_name = "Flores baseline + full developmental model"
full = runs[full_name]
best = full.loc[full["distance"].idxmin()]

print()
print("=" * 92)
print("BEST FLORES-BASELINE FULL MODEL")
print("=" * 92)
print(best.to_string())

print()
print("DECOMPOSITION OF BEST PHENOTYPE")
print("-" * 60)
print(f"Flores baseline linear scale : {best['baseline_linear_scale']:.4f}")
print(f"Flores baseline femur        : {best['baseline_femur']:.2f} mm")
print(f"Flores baseline ICV          : {best['baseline_icv']:.2f} cc")
print(f"Additional femur loss        : {best['developmental_femur_loss']*100:.2f}%")
print(f"Additional brain loss        : {best['developmental_brain_loss']*100:.2f}%")
print(f"Final femur                  : {best['femur']:.2f} mm")
print(f"Final ICV                    : {best['icv']:.2f} cc")

# How far LB1 is from the BEST model's sampled Flores baseline.
baseline_femur_z = (
    LB1["femur"] - best["baseline_femur"]
) / REF["femur_sd"]

baseline_icv_z = (
    LB1["icv"] - best["baseline_icv"]
) / REF["icv_sd"]

print()
print("LB1 DEVIATION FROM BEST SAMPLED FLORES BASELINE")
print("-" * 60)
print(
    "Femur difference relative to modern-reference SD:",
    f"{baseline_femur_z:.3f}"
)
print(
    "ICV difference relative to modern-reference SD:",
    f"{baseline_icv_z:.3f}"
)

# ============================================================
# 12. SAVE OUTPUTS
# ============================================================

summary.to_csv(
    os.path.join(
        BASE,
        "LB1_v12_population_baseline_summary.csv"
    ),
    index=False
)

for name, df in runs.items():
    safe = (
        name.lower()
        .replace(";", "")
        .replace("+", "plus")
        .replace(" ", "_")
    )

    df.nsmallest(
        100,
        "distance"
    ).to_csv(
        os.path.join(
            BASE,
            f"LB1_v12_best_100_{safe}.csv"
        ),
        index=False
    )

# Explicit assumptions table.
assumptions = pd.DataFrame([
    {
        "Parameter": "Flores linear body scale",
        "Lower": FLORES_LINEAR_SCALE_BOUNDS[0],
        "Upper": FLORES_LINEAR_SCALE_BOUNDS[1],
        "Status": "Fossil-constrained sensitivity prior",
        "Rationale":
            "Small body size established by Mata Menge; fossil record too sparse for a true population distribution."
    },
    {
        "Parameter": "Flores brain linear exponent",
        "Lower": FLORES_BRAIN_LINEAR_EXPONENT_BOUNDS[0],
        "Upper": FLORES_BRAIN_LINEAR_EXPONENT_BOUNDS[1],
        "Status": "Allometric sensitivity prior",
        "Rationale":
            "Tests uncertain brain-body scaling rather than assuming modern ICV remains unchanged."
    },
    {
        "Parameter": "Multigenerational environmental state",
        "Lower": 0.0,
        "Upper": 1.0,
        "Status": "Exploratory susceptibility state",
        "Rationale":
            "Modifies developmental susceptibility; never directly shrinks anatomy."
    }
])

assumptions.to_csv(
    os.path.join(
        BASE,
        "LB1_v12_population_baseline_assumptions.csv"
    ),
    index=False
)

# ============================================================
# 13. FIGURES
# ============================================================

plt.figure(figsize=(13, 7))
plt.bar(
    summary["Model"],
    summary["Best Distance"]
)
plt.ylabel("Best Five-Trait Standardized Distance")
plt.title(
    "Version 12: Effect of Flores Population Baseline"
)
plt.xticks(
    rotation=40,
    ha="right"
)
plt.tight_layout()
plt.savefig(
    os.path.join(
        BASE,
        "LB1_v12_population_baseline_comparison.png"
    ),
    dpi=300
)
plt.close()

# Baseline vs final phenotype decomposition.
labels = [
    "Femur (mm)",
    "ICV (cc)"
]

baseline_vals = [
    best["baseline_femur"],
    best["baseline_icv"]
]

final_vals = [
    best["femur"],
    best["icv"]
]

lb1_vals = [
    LB1["femur"],
    LB1["icv"]
]

# Normalize each to LB1 for a common plotting scale.
x = np.arange(2)
width = .24

plt.figure(figsize=(9, 6))
plt.bar(
    x - width,
    np.array(baseline_vals) / np.array(lb1_vals),
    width,
    label="Sampled Flores baseline"
)
plt.bar(
    x,
    np.array(final_vals) / np.array(lb1_vals),
    width,
    label="After developmental perturbation"
)
plt.bar(
    x + width,
    np.ones(2),
    width,
    label="LB1 target"
)

plt.axhline(1.0, linewidth=1)
plt.xticks(x, labels)
plt.ylabel("Value / LB1 target")
plt.title(
    "Population Baseline vs Developmental Perturbation"
)
plt.legend()
plt.tight_layout()
plt.savefig(
    os.path.join(
        BASE,
        "LB1_v12_baseline_to_LB1_decomposition.png"
    ),
    dpi=300
)
plt.close()

# Phenotype space.
plt.figure(figsize=(10, 8))

for name in [
    "Modern baseline + full developmental model",
    "Flores allometric baseline; no developmental insult",
    "Flores baseline + full developmental model"
]:
    df = runs[name]
    sample = df.sample(
        min(3000, len(df)),
        random_state=1
    )

    plt.scatter(
        sample["femur"],
        sample["icv"],
        s=5,
        alpha=.12,
        label=name
    )

plt.scatter(
    LB1["femur"],
    LB1["icv"],
    s=210,
    marker="*",
    label="LB1"
)

plt.xlabel("Femur Length (mm)")
plt.ylabel("Endocranial Volume (cc)")
plt.title(
    "Version 12: Population Baseline and Developmental Phenotype Space"
)
plt.legend()
plt.tight_layout()
plt.savefig(
    os.path.join(
        BASE,
        "LB1_v12_phenotype_space.png"
    ),
    dpi=300
)
plt.close()

# ============================================================
# 14. INTERPRETATION
# ============================================================

print()
print("=" * 92)
print("VERSION 12 INTERPRETATION")
print("=" * 92)

print("""
Version 12 explicitly separates population-level small body size from
individual developmental perturbation.

This is biologically motivated by the Flores fossil record:
small body size was present at Mata Menge by ~700 ka, and therefore predates
LB1 by hundreds of thousands of years.

The endocrine model is no longer responsible for generating the entire
small-bodied phenotype from an average modern human.

Instead:
    1. a broad small-bodied Flores baseline is sampled;
    2. uncertain body-brain allometry determines the population-level ICV
       baseline in the allometric experiments;
    3. IGF, iodine-thyroid, and recurrent maternal-environment mechanisms
       generate additional individual developmental deviations.

The body-only Flores baseline experiment is included specifically to prevent
the analysis from hiding the effect of the uncertain brain-allometry assumption.

A better fit under the Flores baseline does not prove the developmental
hypothesis. It demonstrates that conclusions depend strongly on choosing an
appropriate source-population baseline.

The fossil record remains too sparse to estimate true Flores population means,
standard deviations, or covariance. Consequently the Flores baseline is a
fossil-constrained sensitivity analysis rather than a reconstructed population
distribution.

Future work should replace this prior as additional non-LB1 Liang Bua and
Mata Menge postcranial measurements become available and should use a
covariance-aware multivariate likelihood when a suitable comparative dataset
can be assembled.
""")

print("VERSION 12 COMPLETE")


# ============================================================
# VERSION 13 FINAL THESIS FREEZE
# ============================================================
# The Version 12 architecture above is retained unchanged as the biological
# core. Version 13 adds transparency, structural-score robustness, frozen
# prior-width robustness, and global module-level sensitivity.
#
# IMPORTANT: Do not retune the frozen parameter bounds after inspecting the
# definitive high-N output. Any later changes should be labeled post-hoc.
# ============================================================

V13_REGISTRY = pd.DataFrame([
    ["Flores baseline","linear body scale",0.64,0.80,"fossil-constrained sensitivity prior","Mata Menge supports long-term diminutive body size; exact population distribution unknown"],
    ["Flores baseline","brain linear exponent",1.6,2.2,"allometric sensitivity prior","Tests uncertain population-level brain/body scaling"],
    ["IGF","start week",14.0,30.0,"sensitivity prior","Developmental exposure window"],
    ["IGF","duration",4.0,14.0,"sensitivity prior","Developmental exposure duration"],
    ["IGF","severity",0.20,1.00,"sensitivity prior","Dimensionless perturbation burden"],
    ["IGF","bone coupling",0.55,1.00,"sensitivity prior","Skeletal response"],
    ["IGF","brain/bone coupling ratio",0.25,0.75,"directionally constrained","Cranial effect constrained relative to skeletal effect"],
    ["Iodine-thyroid","iodine deficiency burden",0.0,1.0,"sensitivity prior","Abstract burden, not urinary iodine concentration"],
    ["Iodine-thyroid","thyroid suppression coupling",0.25,1.00,"sensitivity prior","Iodine burden to thyroid-signal suppression"],
    ["Iodine-thyroid","start week",4.0,24.0,"sensitivity prior","Includes early maternal-thyroid-dependent neural development"],
    ["Iodine-thyroid","duration",2.0,24.0,"sensitivity prior","Exposure duration"],
    ["Iodine-thyroid","brain coupling",0.30,1.00,"directionally constrained","Neural/cranial effect"],
    ["Iodine-thyroid","bone coupling",0.00,0.35,"directionally constrained","Skeletal effect constrained below cranial effect"],
    ["Multigenerational","intergenerational retention",0.05,0.50,"exploratory","Environmental/maternal-state persistence; not genetic inheritance"],
    ["Multigenerational","maternal state coupling",0.05,0.30,"exploratory","Environmental burden to vulnerability state"],
    ["Multigenerational","susceptibility gain",0.00,0.50,"exploratory","Background state effect on acute pathway susceptibility"],
    ["Segments","tibia/femur loss multiplier",0.88,1.08,"sensitivity prior","Segment-specific response"],
    ["Segments","humerus/femur loss multiplier",0.62,0.92,"sensitivity prior","Relative arm sparing"],
    ["Segments","foot/femur loss multiplier",0.45,0.80,"sensitivity prior","Relative foot sparing"],
], columns=["Module","Parameter","Lower","Upper","Status","Interpretation"])
V13_REGISTRY.to_csv(os.path.join(BASE,"LB1_v13_parameter_registry.csv"),index=False)

# ------------------------------------------------------------
# Correlation-adjusted score (ROBUSTNESS ONLY)
# ------------------------------------------------------------
# This matrix is structural, not an empirical Flores covariance estimate.
# It tests whether conclusions depend on treating the five standardized
# endpoints as independent despite shared femur denominators in three traits.
V13_R = np.array([
    [1.00, 0.00,-0.25,-0.35,-0.35],
    [0.00, 1.00, 0.00, 0.00, 0.00],
    [-0.25,0.00, 1.00, 0.20, 0.15],
    [-0.35,0.00, 0.20, 1.00, 0.30],
    [-0.35,0.00, 0.15, 0.30, 1.00],
],dtype=float)
V13_R += np.eye(5)*1e-6
V13_R_INV=np.linalg.inv(V13_R)

def v13_z_matrix(df):
    return np.column_stack([
        (df["femur"].to_numpy()-LB1["femur"])/REF["femur_sd"],
        (df["icv"].to_numpy()-LB1["icv"])/REF["icv_sd"],
        (df["crural_index"].to_numpy()-LB1["crural_index"])/REF["crural_sd"],
        (df["humerofemoral_index"].to_numpy()-LB1["humerofemoral_index"])/REF["humerofemoral_sd"],
        (df["foot_femur_index"].to_numpy()-LB1["foot_femur_index"])/REF["foot_femur_sd"],
    ])

def v13_corr_score(df):
    Z=v13_z_matrix(df)
    return np.einsum("ij,jk,ik->i",Z,V13_R_INV,Z)

corr_rows=[]
for name,df in runs.items():
    cs=v13_corr_score(df)
    corr_rows.append({
        "Model":name,
        "Best correlation-adjusted score":float(np.min(cs)),
        "Median correlation-adjusted score":float(np.median(cs)),
    })
V13_CORR=pd.DataFrame(corr_rows).sort_values("Best correlation-adjusted score")
V13_CORR.to_csv(os.path.join(BASE,"LB1_v13_correlation_adjusted_robustness.csv"),index=False)

print("\n"+"="*92)
print("VERSION 13 CORRELATION-ADJUSTED ROBUSTNESS")
print("="*92)
print(V13_CORR.to_string(index=False))

# ------------------------------------------------------------
# Global module-level sensitivity for the frozen full model
# ------------------------------------------------------------
# Spearman rank correlations are descriptive global sensitivity measures.
# They identify which sampled states are most associated with total score.
full_v13=runs["Flores baseline + full developmental model"]
sens_cols=[
    "baseline_linear_scale","baseline_brain_exponent","baseline_femur","baseline_icv",
    "environmental_burden","multigenerational_state","susceptibility","iodine_burden",
    "developmental_femur_loss","developmental_brain_loss"
]
sens_cols=[c for c in sens_cols if c in full_v13.columns]
sample=full_v13.sample(min(100000,len(full_v13)),random_state=SEED)
score_rank=sample["distance"].rank().to_numpy(float)
sens_rows=[]
for c in sens_cols:
    x=sample[c]
    if float(x.std())==0:
        rho=0.0
    else:
        rho=float(np.corrcoef(x.rank().to_numpy(float),score_rank)[0,1])
    sens_rows.append({"Variable":c,"Spearman_rho_with_score":rho,"Absolute_rho":abs(rho)})
V13_SENS=pd.DataFrame(sens_rows).sort_values("Absolute_rho",ascending=False)
V13_SENS.to_csv(os.path.join(BASE,"LB1_v13_global_module_sensitivity.csv"),index=False)

print("\n"+"="*92)
print("VERSION 13 GLOBAL MODULE-LEVEL SENSITIVITY")
print("="*92)
print(V13_SENS.to_string(index=False))

# ------------------------------------------------------------
# Frozen ±10% Flores-prior-width robustness
# ------------------------------------------------------------
# Rather than changing the biological center of the prior, these tests alter
# only its width around the frozen center (0.72).
def v13_flores_baseline_width(n,width_multiplier=1.0,allometric_brain=True):
    center=0.72
    half=0.08*width_multiplier
    lo=max(0.50,center-half)
    hi=min(0.95,center+half)
    scale=U(lo,hi,n)
    crural=np.clip(rng.normal(REF["crural_mean"],BASELINE_CRURAL_SHIFT_SD,n),77,90)
    hfi=np.clip(rng.normal(REF["humerofemoral_mean"],BASELINE_HFI_SHIFT_SD,n),64,82)
    ffi=np.clip(rng.normal(REF["foot_femur_mean"],BASELINE_FFI_SHIFT_SD,n),47,63)
    femur=REF["femur_mean"]*scale
    tibia=femur*crural/100
    humerus=femur*hfi/100
    foot=femur*ffi/100
    if allometric_brain:
        exp=U(FLORES_BRAIN_LINEAR_EXPONENT_BOUNDS[0],FLORES_BRAIN_LINEAR_EXPONENT_BOUNDS[1],n)
        icv=REF["icv_mean"]*np.power(scale,exp)
    else:
        exp=np.zeros(n); icv=np.full(n,REF["icv_mean"])
    return {"baseline_type":np.array(["V13 robustness"]*n),"linear_scale":scale,"brain_exponent":exp,
            "femur":femur,"tibia":tibia,"humerus":humerus,"foot":foot,"icv":icv}

# Re-use the frozen developmental pathways from Version 12, changing only baseline width.
def v13_simulate_prior_width(label,width_multiplier,n):
    baseline=v13_flores_baseline_width(n,width_multiplier,True)
    igf_bone,igf_brain=igf_losses(n)
    iodine_bone,iodine_brain,iodine_burden=iodine_losses(n)
    generations,env,mg_state,susceptibility=multigenerational_susceptibility(n)
    igf_bone=np.clip(igf_bone*susceptibility,0,.95); igf_brain=np.clip(igf_brain*susceptibility,0,.95)
    iodine_bone=np.clip(iodine_bone*susceptibility,0,.95); iodine_brain=np.clip(iodine_brain*susceptibility,0,.95)
    total_bone=1-(1-igf_bone)*(1-iodine_bone); total_brain=1-(1-igf_brain)*(1-iodine_brain)
    total_bone=np.clip(total_bone,0,.95); total_brain=np.clip(total_brain,0,.95)
    iod_frac=np.clip(iodine_bone/np.maximum(total_bone,1e-12),0,1)
    limbs=apply_segment_response(baseline,total_bone,iod_frac,n)
    icv=baseline["icv"]*(1-total_brain)
    score,crural,hfi,ffi,comps=phenotype_score(limbs["femur"],icv,limbs["tibia"],limbs["humerus"],limbs["foot"])
    return pd.DataFrame({"model":label,"distance":score,"femur":limbs["femur"],"icv":icv,
                         "crural_index":crural,"humerofemoral_index":hfi,"foot_femur_index":ffi})

robust_n=min(100000,N)
robust_rows=[]
for mult,label in [(0.90,"Flores prior narrowed 10%"),(1.00,"Flores prior frozen"),(1.10,"Flores prior widened 10%")]:
    df=v13_simulate_prior_width(label,mult,robust_n)
    b=df.loc[df["distance"].idxmin()]
    robust_rows.append({"Scenario":label,"N":len(df),"Best score":b["distance"],"Median score":df["distance"].median(),
                        "Best femur":b["femur"],"Best ICV":b["icv"],"P(D<10)":(df["distance"]<10).mean(),"P(D<20)":(df["distance"]<20).mean()})
V13_ROBUST=pd.DataFrame(robust_rows).sort_values("Best score")
V13_ROBUST.to_csv(os.path.join(BASE,"LB1_v13_prior_width_robustness.csv"),index=False)
print("\n"+"="*92)
print("VERSION 13 FROZEN PRIOR-WIDTH ROBUSTNESS")
print("="*92)
print(V13_ROBUST.to_string(index=False))

# Component-error registry for the best full model.
best_v13=full_v13.loc[full_v13["distance"].idxmin()]
V13_COMPONENTS=pd.DataFrame({
    "Endpoint":["Femur","ICV","Crural index","Humerofemoral index","Foot/Femur index"],
    "Z":[
        (best_v13["femur"]-LB1["femur"])/REF["femur_sd"],
        (best_v13["icv"]-LB1["icv"])/REF["icv_sd"],
        (best_v13["crural_index"]-LB1["crural_index"])/REF["crural_sd"],
        (best_v13["humerofemoral_index"]-LB1["humerofemoral_index"])/REF["humerofemoral_sd"],
        (best_v13["foot_femur_index"]-LB1["foot_femur_index"])/REF["foot_femur_sd"],
    ]
})
V13_COMPONENTS["Squared_Error"]=V13_COMPONENTS["Z"]**2
V13_COMPONENTS.to_csv(os.path.join(BASE,"LB1_v13_best_component_errors.csv"),index=False)

# Final figures.
plt.figure(figsize=(10,6))
top=V13_SENS.head(10).iloc[::-1]
plt.barh(top["Variable"],top["Spearman_rho_with_score"])
plt.xlabel("Spearman rank correlation with phenotype score")
plt.title("Version 13 Global Module-Level Sensitivity")
plt.tight_layout(); plt.savefig(os.path.join(BASE,"LB1_v13_global_module_sensitivity.png"),dpi=300); plt.close()

plt.figure(figsize=(9,6))
plt.bar(V13_COMPONENTS["Endpoint"],V13_COMPONENTS["Squared_Error"])
plt.ylabel("Squared standardized error")
plt.title("Version 13 Best Full-Model Error by Endpoint")
plt.xticks(rotation=25,ha="right")
plt.tight_layout(); plt.savefig(os.path.join(BASE,"LB1_v13_best_component_errors.png"),dpi=300); plt.close()

print("\n"+"="*92)
print("VERSION 13 FINAL THESIS FREEZE RULES")
print("="*92)
print("""
1. Report the final high-N output without retuning parameter bounds.
2. Separate empirical inputs from sensitivity/exploratory assumptions using the registry.
3. Report both standard and correlation-adjusted model rankings.
4. Report global module-level sensitivity and prior-width robustness.
5. Treat a close fit as physiological compatibility, not historical causation.
6. Treat a poor fit as failure of this implementation, not proof against all developmental hypotheses.
7. Label any later parameter changes or new mechanisms as post-hoc analyses.
""")
print("VERSION 13 FINAL COMPLETE")
