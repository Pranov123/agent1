# ── Agent 1 Configuration ─────────────────────────────────────
# Swap these values when moving to company server

# Model provider — "groq" for local dev, "ollama" for company server
PROVIDER = "groq"

# Groq settings (local development)
import os
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_BASE_URL = "https://api.groq.com/openai/v1"
GROQ_PRIMARY_MODEL   = "llama-3.3-70b-versatile"  # replaces Qwen3
GROQ_VALIDATION_MODEL = "llama-3.3-70b-versatile"  # replaces DeepSeek R1

# Ollama settings (company server)
OLLAMA_BASE_URL = "http://localhost:11434/v1"
OLLAMA_PRIMARY_MODEL    = "qwen3:32b"
OLLAMA_VALIDATION_MODEL = "deepseek-r1:32b"

# Pipeline settings
MAX_CLARIFICATION_ROUNDS = 3
ETHOS_CONFIDENCE_THRESHOLD_HIGH      = 0.72
ETHOS_CONFIDENCE_THRESHOLD_UNCERTAIN = 0.50

# Timeout
REQUEST_TIMEOUT = 600.0

# Paths
OUTPUT_DIR = "output"
LOG_DIR    = "logs"