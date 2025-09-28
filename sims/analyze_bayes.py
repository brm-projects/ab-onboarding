import os, sys, numpy as np, pandas as pd
from sqlalchemy import create_engine, text

EXPERIMENT = os.getenv("EXPERIMENT", "onboarding_progressive_v1")
DB_URL     = os.getenv("DATABASE_URL", "postgresql+psycopg://postgres:postgres@localhost:5432/abdb")
SCHEMA     = os.getenv("DBT_MART_SCHEMA", "analytics")
ROPE       = float(os.getenv("ROPE", "0.005"))  # absolute diff threshold (e.g. 0.5 pp)
DECISION_PR= float(os.getenv("DECISION_PR", "0.95"))
ALPHA_PRIOR_A = float(os.getenv("BETA_ALPHA", "1.0"))
BETA_PRIOR_B  = float(os.getenv("BETA_BETA",  "1.0"))

SQL = f"""
select variant,
       count(*)::int             as n_users,
       sum(converted::int)::int  as n_converted,
       sum(kyc_7d::int)::int     as n_kyc
from {SCHEMA}.fct_conversions
where experiment_key = :exp
group by variant
order by variant;
"""

def hdi(x, cred=0.95):
    x = np.sort(x)
    n = x.size
    k = int(np.floor(cred * n))
    widths = x[k:] - x[:n-k]
    i = np.argmin(widths)
    return float(x[i]), float(x[i+k])

def main():
    print("[info] DB:", DB_URL)
    print("[info] Schema:", SCHEMA)
    eng = create_engine(DB_URL, pool_pre_ping=True)
    with eng.connect() as con:
        df = pd.read_sql(text(SQL), con, params={"exp": EXPERIMENT})
    if df.empty or set(df["variant"]) != {"A","B"}:
        print("[error] Need two variants (A,B) with data. Run simulator + `dbt run`.")
        sys.exit(1)
    df = df.sort_values("variant").reset_index(drop=True)

    # Counts
    nA, nB = int(df.loc[0,"n_users"]),     int(df.loc[1,"n_users"])
    cA, cB = int(df.loc[0,"n_converted"]), int(df.loc[1,"n_converted"])
    kA, kB = int(df.loc[0,"n_kyc"]),       int(df.loc[1,"n_kyc"])

    print("\n[info] Counts:")
    print(df.to_string(index=False))

    # Conjugate Beta posteriors for conversion rates
    aA, bA = ALPHA_PRIOR_A + cA, BETA_PRIOR_B + (nA - cA)
    aB, bB = ALPHA_PRIOR_A + cB, BETA_PRIOR_B + (nB - cB)

    rng = np.random.default_rng(42)
    sA = rng.beta(aA, bA, size=200_000)
    sB = rng.beta(aB, bB, size=200_000)
    lift = sB - sA

    prob_B_better = float((lift > 0).mean())
    prob_in_rope  = float((np.abs(lift) <= ROPE).mean())
    hdi_low, hdi_high = hdi(lift, 0.95)

    # Guardrail: KYC≤7d (frequentist rate report)
    kyc_rate_A = kA / nA if nA else 0.0
    kyc_rate_B = kB / nB if nB else 0.0
    delta_kyc  = kyc_rate_B - kyc_rate_A
    non_inferior = (kyc_rate_A - kyc_rate_B) <= 0.02  # allow up to 2 pp worse

    print("\n=== Bayesian Results (conjugate Beta–Binomial) ===")
    print(f"Pr(B > A) = {prob_B_better:.3f}")
    print(f"Lift 95% HDI = [{hdi_low:+.4f}, {hdi_high:+.4f}]")
    print(f"Pr(|lift| ≤ {ROPE:.3f}) = {prob_in_rope:.3f}  (practical equivalence)")

    print("\n[guardrail] KYC≤7d:")
    print(f"A={kyc_rate_A:.4f}  B={kyc_rate_B:.4f}  Δ(B−A)={delta_kyc:+.4f}")
    print("KYC guardrail:", "PASS (non-inferior)" if non_inferior else "FAIL (worse than 2 pp)")

    ship = (prob_B_better >= DECISION_PR) and non_inferior

    print("\n=== Interpretation ===")
    if ship:
        print("High posterior probability that B improves conversion (≥ 95%), "
              "and KYC guardrail passes. Recommend SHIP Variant B.")
    elif prob_in_rope >= DECISION_PR:
        print("Difference is practically negligible (within ROPE). Either variant is acceptable; "
              "choose based on secondary criteria.")
    else:
        print("Evidence not decisive or guardrail fails. Recommend HOLD and collect more data / investigate.")

if __name__ == "__main__":
    main()
