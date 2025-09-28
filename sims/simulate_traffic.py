import os, random, time, requests

API = os.getenv("API_BASE", "http://127.0.0.1:8000")
EXPERIMENT = "onboarding_progressive_v1"

def assign(user_id: str) -> str:
    r = requests.get(f"{API}/assign", params={"user_id": user_id, "experiment": EXPERIMENT}, timeout=5)
    r.raise_for_status()
    return r.json()["variant"]

def event(user_id: str, variant: str, event_type: str, metadata=None):
    payload = {
        "user_id": user_id,
        "experiment_key": EXPERIMENT,
        "variant": variant,
        "event_type": event_type,
    }
    if metadata:
        payload["metadata"] = metadata
    r = requests.post(f"{API}/event", json=payload, timeout=5)
    r.raise_for_status()

def main(
    n_users=3000,
    p_complete_A=0.40,
    p_complete_B=0.55,
    p_kyc_within7=0.80,
    seed=42
):
    random.seed(seed)
    for i in range(n_users):
        user_id = f"u{i:06d}"
        variant = assign(user_id)

        # everyone starts signup
        md = {
            "device": random.choice(["ios","android","web"]),
            "country": random.choice(["FR","DE","ES","IT","NL"])
        }
        event(user_id, variant, "signup_start", md)

        # convert with different probabilities by variant
        p = p_complete_B if variant == "B" else p_complete_A
        if random.random() < p:
            event(user_id, variant, "signup_complete")
            if random.random() < p_kyc_within7:
                event(user_id, variant, "kyc_complete")

        if i and i % 500 == 0:
            print(f"{i} users simulated")

if __name__ == "__main__":
    main()
