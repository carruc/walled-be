import os

# Runpod credentials and settings from environment
RUNPOD_API_KEY = os.getenv("RUNPOD_API_KEY")
RUNPOD_SL_ID = os.getenv("RUNPOD_SL_ID")

# Feature toggle and polling settings
GUARDRAIL_PI_ENABLED = os.getenv("GUARDRAIL_PI_ENABLED", "true").lower() == "true"
RUNPOD_POLL_INTERVAL_S = float(os.getenv("RUNPOD_POLL_INTERVAL_S", "1.0"))
RUNPOD_MAX_WAIT_S = float(os.getenv("RUNPOD_MAX_WAIT_S", "60.0"))
