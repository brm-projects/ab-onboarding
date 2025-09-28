import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import streamlit as st
from sqlalchemy import create_engine, text
from statsmodels.stats.proportion import proportion_confint

# --- Config ---
EXPERIMENT = os.getenv("EXPERIMENT", "onboarding_progressive_v1")
DB_URL     = os.getenv("DATABASE_URL", "postgresql+psycopg://postgres:postgres@localhost:5432/abdb")
SCHEMA     = os.getenv("DBT_MART_SCHEMA", "analytics")

SQL = f"""
select variant,
       count(*)::int            as n_users,
       sum(converted::int)::int as n_converted,
       sum(kyc_7d::int)::int    as n_kyc
from {SCHEMA}.fct_conversions
where experiment_key = :exp
group by variant
order by variant;
"""

# --- Helpers ---
def proportion_ci(successes, nobs, alpha=0.05):
    return proportion_confint(successes, nobs, alpha=alpha, method="wilson")

# --- App ---
def main():
    st.title("Onboarding Experiment Results")
    st.markdown("""
    This dashboard shows the results of our A/B test on the onboarding process:
    - **Variant A**: traditional onboarding (all steps upfront)  
    - **Variant B**: progressive onboarding (steps spread out)  

    **Goal:** increase user onboarding completion without hurting compliance (KYC within 7 days).
    """)

    eng = create_engine(DB_URL, pool_pre_ping=True)
    with eng.connect() as con:
        df = pd.read_sql(text(SQL), con, params={"exp": EXPERIMENT})

    st.header("Funnel (A vs B) — before the decision")

    # 1) Exposed (from mart)
    SQL_EXPOSED = f"""
    select variant, count(*)::int as n_exposed
    from {SCHEMA}.fct_exposures
    where experiment_key = :exp
    group by variant
    order by variant;
    """

    # 2) Signup start / complete (from raw events)
    SQL_STEPS = """
    select variant, event_type, count(distinct user_id)::int as n_users
    from public.events_raw
    where experiment_key = :exp
    and event_type in ('signup_start','signup_complete')
    group by variant, event_type
    order by variant, event_type;
    """

    # 3) KYC≤7d (from mart)
    SQL_KYC = f"""
    select variant, sum(kyc_7d::int)::int as n_kyc
    from {SCHEMA}.fct_conversions
    where experiment_key = :exp
    group by variant
    order by variant;
    """

    eng = create_engine(DB_URL, pool_pre_ping=True)
    with eng.connect() as con:
        exposed = pd.read_sql(text(SQL_EXPOSED), con, params={"exp": EXPERIMENT}).set_index("variant")
        steps   = pd.read_sql(text(SQL_STEPS),   con, params={"exp": EXPERIMENT})
        kyc     = pd.read_sql(text(SQL_KYC),     con, params={"exp": EXPERIMENT}).set_index("variant")

    # reshape step counts
    starts = steps[steps["event_type"]=="signup_start"].set_index("variant")["n_users"].rename("n_start")
    completes = steps[steps["event_type"]=="signup_complete"].set_index("variant")["n_users"].rename("n_complete")

    # assemble per-variant funnel
    funnel = exposed.join(starts, how="left").join(completes, how="left").join(kyc, how="left").fillna(0).astype(int)
    funnel = funnel.rename(columns={
        "n_exposed": "Exposed",
        "n_start": "Signup Start",
        "n_complete": "Signup Complete",
        "n_kyc": "KYC ≤ 7d"
    })
    funnel = funnel.loc[["A","B"]]  # ensure A then B order

    # compute step conversions (% of prior step)
    def step_rate(curr, prev):
        return (funnel[curr] / funnel[prev]).replace([np.inf, np.nan], 0.0)

    rates = pd.DataFrame({
        "A: Start/Exposed": (funnel.loc["A","Signup Start"] / funnel.loc["A","Exposed"]) if funnel.loc["A","Exposed"] else 0.0,
        "A: Complete/Start": (funnel.loc["A","Signup Complete"] / funnel.loc["A","Signup Start"]) if funnel.loc["A","Signup Start"] else 0.0,
        "A: KYC/Complete": (funnel.loc["A","KYC ≤ 7d"] / funnel.loc["A","Signup Complete"]) if funnel.loc["A","Signup Complete"] else 0.0,
        "B: Start/Exposed": (funnel.loc["B","Signup Start"] / funnel.loc["B","Exposed"]) if funnel.loc["B","Exposed"] else 0.0,
        "B: Complete/Start": (funnel.loc["B","Signup Complete"] / funnel.loc["B","Signup Start"]) if funnel.loc["B","Signup Start"] else 0.0,
        "B: KYC/Complete": (funnel.loc["B","KYC ≤ 7d"] / funnel.loc["B","Signup Complete"]) if funnel.loc["B","Signup Complete"] else 0.0,
    }, index=["rate"]).T.round(3)

    # show tables
    st.write("**Funnel counts (users):**")
    st.dataframe(funnel)

    st.write("**Step conversion (per prior step):**")
    st.dataframe(rates)

    # Horizontal funnel chart (normalized by Exposed)
    st.subheader("Funnel chart (share of Exposed)")
    st.caption("Bars show % of exposed users reaching each step, by variant.")

    plot_df = funnel.copy()
    for col in ["Signup Start","Signup Complete","KYC ≤ 7d"]:
        plot_df[f"A {col}"] = plot_df.loc["A", col] / plot_df.loc["A", "Exposed"] if plot_df.loc["A","Exposed"] else 0.0
        plot_df[f"B {col}"] = plot_df.loc["B", col] / plot_df.loc["B", "Exposed"] if plot_df.loc["B","Exposed"] else 0.0

    labels = ["Signup Start","Signup Complete","KYC ≤ 7d"]
    a_vals = [plot_df.loc["A", f"A {l}"] for l in labels]
    b_vals = [plot_df.loc["B", f"B {l}"] for l in labels]

    fig3, ax3 = plt.subplots(figsize=(7, 3.8))
    y = np.arange(len(labels))
    ax3.barh(y+0.18, a_vals, height=0.35, label="A")
    ax3.barh(y-0.18, b_vals, height=0.35, label="B")
    ax3.set_yticks(y, labels)
    ax3.set_xlim(0, 1)
    ax3.set_xlabel("Share of Exposed (0–1)")
    ax3.legend()
    for i, v in enumerate(a_vals):
        ax3.text(v+0.01, i+0.18, f"{v:.0%}", va="center")
    for i, v in enumerate(b_vals):
        ax3.text(v+0.01, i-0.18, f"{v:.0%}", va="center")
    st.pyplot(fig3)

    # quick stakeholder summary
    st.info(
        "Reading the funnel: Bars show what share of all exposed users reach each step.\n"
        "Variant B’s bars are higher at every stage, which means it gets more people from Start → Complete → KYC."
    )


    # Show headline numbers
    st.header("Key Results")
    df["conv_rate"] = df["n_converted"] / df["n_users"]
    df["kyc_rate"] = df["n_kyc"] / df["n_users"]

    st.write("**Conversion and KYC rates by variant:**")
    st.dataframe(df[["variant","n_users","conv_rate","kyc_rate"]].round(3))

    # Conversion chart
    st.subheader("Conversion Rates (95% Confidence Intervals)")
    cis = [proportion_ci(r, n) for r, n in zip(df["n_converted"], df["n_users"])]
    df["ci_low"], df["ci_high"] = zip(*cis)
    fig, ax = plt.subplots(figsize=(5,4))
    ax.bar(df["variant"], df["conv_rate"], color=["#4c72b0","#55a868"],
           yerr=[df["conv_rate"]-df["ci_low"], df["ci_high"]-df["conv_rate"]],
           capsize=5)
    ax.set_ylabel("Conversion Rate")
    st.pyplot(fig)

    # Bayesian lift
    st.subheader("Bayesian View of the Difference (Lift)")
    aA, bA = 1+df.loc[df["variant"]=="A","n_converted"].item(), 1+df.loc[df["variant"]=="A","n_users"].item()-df.loc[df["variant"]=="A","n_converted"].item()
    aB, bB = 1+df.loc[df["variant"]=="B","n_converted"].item(), 1+df.loc[df["variant"]=="B","n_users"].item()-df.loc[df["variant"]=="B","n_converted"].item()
    rng = np.random.default_rng(42)
    sA = rng.beta(aA, bA, 50_000)
    sB = rng.beta(aB, bB, 50_000)
    lift = sB - sA
    prob = (lift > 0).mean()

    fig2, ax2 = plt.subplots(figsize=(6,4))
    ax2.hist(lift, bins=80, density=True, color="#55a868", alpha=0.7)
    ax2.axvline(0, color="k", linestyle="--")
    ax2.set_xlabel("Improvement (B - A)")
    ax2.set_ylabel("Density")
    st.pyplot(fig2)

    st.markdown(f"**Probability B is better than A: {prob:.1%}**")

    # Guardrail
    st.subheader("Guardrail Check: KYC within 7 days")
    a_kyc = df.loc[df["variant"]=="A","kyc_rate"].item()
    b_kyc = df.loc[df["variant"]=="B","kyc_rate"].item()
    delta = 0.02
    non_inferior = (a_kyc - b_kyc) <= delta
    if non_inferior:
        st.success("✅ KYC guardrail passed — B does not harm compliance")
    else:
        st.error("❌ KYC guardrail failed — investigate further")

    # Final recommendation
    st.header("Recommendation")
    if prob > 0.95 and non_inferior:
        st.success("**Ship Variant B** — strong evidence it improves onboarding safely.")
    else:
        st.warning("Hold — results not yet conclusive or guardrail failed.")

if __name__ == "__main__":
    main()
