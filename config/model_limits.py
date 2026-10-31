from typing import Dict, Any

MODEL_LIMITS: Dict[str, Dict[str, Any]] = {
    "Agent Antigravity": {
        "rpm": 60,
        "tpm": 100000,
        "rpd": 100,
        "skip_request_count": True
    },
    "Gemma 4 26B": {
        "rpm": 30,
        "tpm": 16000,
        "rpd": 14400,
        "skip_request_count": False
    },
    "Gemma 4 31B": {
        "rpm": 30,
        "tpm": 16000,
        "rpd": 14400,
        "skip_request_count": False
    },
    "Gemini 3.8 Flash TTS": {
        "rpm": 3,
        "tpm": 10000,
        "rpd": 10,
        "skip_request_count": False
    }
}

MODEL_IDENTIFIER_MAPPING: Dict[str, str] = {
    "Agent Antigravity": "gemini-2.5-pro",
    "Gemma 4 26B": "gemma-2-27b-it",
    "Gemma 4 31B": "gemma-2-27b-it",
    "Gemini 3.8 Flash TTS": "gemini-2.5-flash"
}