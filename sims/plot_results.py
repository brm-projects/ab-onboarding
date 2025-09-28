import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sqlalchemy import create_engine, text

EXPERIMENT = os.getenv("EXPERIMENT", "onboarding_progressive_v1")
DB_URL     = os.getenv("DATABASE_URL", "postgresql+psycopg://postgres:postgres@localhost:5432/abdb")
SCHEMA     = os.getenv("DBT_MART_SCHEMA", "analytics")

SQL = f"""
select variant,
       count(*)::int            as n_users,
       sum(converted::int)::int as n_converted
from {SCHEMA}.fct_conversions
where experiment_key = :exp
group by variant
order by variant;
"""

def proportion_confint(successes, nobs, alpha=0.05):
    """Wilson score interval for a binomial proportion"""
    from statsmodels.stats.proportion import proportion_confint
    return proportion_confint(successes, nobs, alpha=alpha, method="wilson")

def main():
    eng = create_engine(DB_URL, pool_pre_ping=True)
    with eng.connect() as con:
        df = pd.read_sql(text(SQL), con, params={"exp": EXPERIMENT})
    df = df.sort_values("variant").reset_index(drop=True)
    df["rate"] = df["n_converted"] / df["n_users"]

    # 1) Conversion rate bar chart with CI
    cis = [proportion_confint(r, n) for r, n in zip(df["n_converted"], df["n_users"])]
    df["ci_low"] = [lo for lo, hi in cis]
    df["ci_high"] = [hi for lo, hi in cis]

    plt.figure(figsize=(5,4))
    plt.bar(df["variant"], df["rate"], yerr=[df["rate"]-df["ci_low"], df["ci_high"]-df["rate"]],
            capsize=5, color=["#4c72b0","#55a868"])
    plt.ylabel("Conversion rate")
    plt.title("Onboarding conversion by variant (95% CI)")
    plt.savefig("results_conversion.png", dpi=150, bbox_inches="tight")

    # 2) Posterior distribution of lift (Beta-Binomial)
    aA, bA = 1+df.loc[df["variant"]=="A","n_converted"].item(), 1+df.loc[df["variant"]=="A","n_users"].item()-df.loc[df["variant"]=="A","n_converted"].item()
    aB, bB = 1+df.loc[df["variant"]=="B","n_converted"].item(), 1+df.loc[df["variant"]=="B","n_users"].item()-df.loc[df["variant"]=="B","n_converted"].item()
    rng = np.random.default_rng(42)
    sA = rng.beta(aA, bA, 100_000)
    sB = rng.beta(aB, bB, 100_000)
    lift = sB - sA

    plt.figure(figsize=(6,4))
    plt.hist(lift, bins=100, density=True, color="#55a868", alpha=0.7)
    plt.axvline(0, color="k", linestyle="--")
    plt.xlabel("Lift (B - A)")
    plt.ylabel("Density")
    plt.title("Posterior distribution of lift")
    plt.savefig("results_lift.png", dpi=150, bbox_inches="tight")

    print("Saved plots: results_conversion.png, results_lift.png")

if __name__ == "__main__":
    main()
