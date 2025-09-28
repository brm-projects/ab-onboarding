# sims/analyze_experiment.py
import os, sys
import pandas as pd
from sqlalchemy import create_engine, text
from statsmodels.stats.proportion import proportions_ztest, proportion_confint

EXPERIMENT = os.getenv("EXPERIMENT", "onboarding_progressive_v1")
DB_URL = os.getenv("DATABASE_URL", "postgresql+psycopg://postgres:postgres@localhost:5432/abdb")
SCHEMA = os.getenv("DBT_MART_SCHEMA", "analytics")

SQL = f"""
select variant,
       count(*)::int                    as n_users,
       sum(converted::int)::int         as n_converted,
       sum(kyc_7d::int)::int            as n_kyc
from {SCHEMA}.fct_conversions
where experiment_key = :exp
group by variant
order by variant;
"""


def main():
    print("[info] Using DB:", DB_URL)
    print("[info] Using schema:", SCHEMA)
    engine = create_engine(DB_URL, pool_pre_ping=True)

    try:
        with engine.connect() as conn:
            df = pd.read_sql(text(SQL), conn, params={"exp": EXPERIMENT})
    except Exception as e:
        print("[error] Query failed:", e)
        print("Hints: ensure dbt built the marts to this schema (`dbt run --project-dir dbt`).")
        sys.exit(1)

    if df.empty:
        print("[info] No rows returned. Run the simulator, then `dbt run`.")
        sys.exit(0)

    print("\n[info] Raw counts:\n", df.to_string(index=False))

    if set(df["variant"]) != {"A","B"}:
        print("[warn] Expected exactly two variants {A,B}, got:", set(df["variant"]))
        sys.exit(0)

    df = df.sort_values("variant").reset_index(drop=True)
    df["rate"] = df["n_converted"] / df["n_users"]
    a, b = df.iloc[0], df.iloc[1]

    stat, pval = proportions_ztest(count=df["n_converted"].to_numpy(),
                                   nobs=df["n_users"].to_numpy())
    ci_a = proportion_confint(int(a["n_converted"]), int(a["n_users"]), method="wilson")
    ci_b = proportion_confint(int(b["n_converted"]), int(b["n_users"]), method="wilson")
    lift = float(b["rate"] - a["rate"])

    print(f"\n=== Experiment: {EXPERIMENT} ===")
    print(f"A: n={int(a['n_users'])}, conv={int(a['n_converted'])}, rate={a['rate']:.4f}, CI95=[{ci_a[0]:.4f}, {ci_a[1]:.4f}]")
    print(f"B: n={int(b['n_users'])}, conv={int(b['n_converted'])}, rate={b['rate']:.4f}, CI95=[{ci_b[0]:.4f}, {ci_b[1]:.4f}]")
    print(f"\nDifference (B - A): {lift:.4f}")
    print(f"z = {stat:.3f}, p = {pval:.6f}")
    print("Decision:", "Statistically significant at 5%." if pval < 0.05 else "Not statistically significant at 5% yet.")


    # --- Guardrail: 7-day KYC completion ---
    df["kyc_rate"] = df["n_kyc"] / df["n_users"]
    a_kyc = df.loc[df["variant"]=="A","kyc_rate"].item()
    b_kyc = df.loc[df["variant"]=="B","kyc_rate"].item()

    # Non-inferiority check: B’s KYC must not be worse than A by >2pp
    delta = 0.02
    non_inferior = (a_kyc - b_kyc) <= delta

    print(f"\nGuardrail (KYC≤7d):")
    print(f"A: rate={a_kyc:.4f}   B: rate={b_kyc:.4f}   Δ(B−A)={b_kyc-a_kyc:+.4f}")
    print("KYC guardrail:", "PASS (non-inferior)" if non_inferior else "FAIL (worse than delta)")

    # Final decision combining primary + guardrail
    ship = (pval < 0.05) and non_inferior
    print("\nRecommendation:", "SHIP Variant B" if ship else "HOLD — investigate guardrails")

    print("\n=== Interpretation ===")

    if pval < 0.05:
        print(f"The difference in conversion between variants A and B is statistically significant (p={pval:.4g}).")
        if ship:
            print("Variant B improves onboarding completion without harming the 7-day KYC rate, "
                "so it is recommended to ship Variant B.")
        else:
            print("Variant B improves onboarding completion, but fails the KYC guardrail. "
                "We recommend holding rollout until the compliance impact is understood.")
    else:
        print("The difference in conversion is not statistically significant yet. "
            "We cannot confidently recommend a winner at this stage.")




if __name__ == "__main__":
    main()
