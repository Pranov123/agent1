# ── Agent 1 Configuration ─────────────────────────────────────
import os

# Your Groq API key
# Get a free key at https://console.groq.com
GROQ_API_KEY = "your_api_key_here"

# Groq settings
GROQ_BASE_URL         = "https://api.groq.com/openai/v1"
GROQ_PRIMARY_MODEL    = "llama-3.3-70b-versatile"
GROQ_VALIDATION_MODEL = "llama-3.3-70b-versatile"

# Pipeline settings
MAX_CLARIFICATION_ROUNDS             = 3
ETHOS_CONFIDENCE_THRESHOLD_HIGH      = 0.72
ETHOS_CONFIDENCE_THRESHOLD_UNCERTAIN = 0.50

# Timeout
REQUEST_TIMEOUT = 600.0

# Paths
OUTPUT_DIR = "output"
LOG_DIR    = "logs"