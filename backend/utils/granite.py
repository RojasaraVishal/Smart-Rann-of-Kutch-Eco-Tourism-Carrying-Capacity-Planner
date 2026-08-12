"""
LLM client — supports Groq API (primary) and IBM Granite via watsonx.ai (secondary).

Priority order:
  1. Groq API  — if GROQ_API_KEY is set
  2. IBM Granite — if IBM_API_KEY and IBM_PROJECT_ID are set
  3. Demo fallback — structured placeholder so the platform works without any credentials

Never expose API keys in responses or logs.
"""
import httpx
from config import get_settings

settings = get_settings()

IAM_TOKEN_URL = "https://iam.cloud.ibm.com/identity/token"
IBM_INFERENCE_URL = (
    f"{settings.ibm_api_url}/ml/v1/text/generation?version=2023-05-29"
)


# ── Groq ──────────────────────────────────────────────────────────────────────

async def _call_groq(
    prompt: str,
    max_new_tokens: int,
    temperature: float,
    system_prompt: str,
) -> dict:
    """Call Groq's OpenAI-compatible chat completions endpoint."""
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})

    payload = {
        "model": settings.groq_model_id,
        "messages": messages,
        "max_tokens": max_new_tokens,
        "temperature": temperature,
        "top_p": 0.9,
    }

    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.post(
            settings.groq_api_url,
            json=payload,
            headers={
                "Authorization": f"Bearer {settings.groq_api_key}",
                "Content-Type": "application/json",
            },
        )
        resp.raise_for_status()
        text = resp.json()["choices"][0]["message"]["content"].strip()
        return {
            "text": text,
            "source": "groq",
            "model": settings.groq_model_id,
            "data_label": "AI",
        }


# ── IBM Granite ───────────────────────────────────────────────────────────────

async def _get_iam_token() -> str:
    """Exchange IBM API key for a short-lived IAM bearer token."""
    async with httpx.AsyncClient(timeout=20) as client:
        resp = await client.post(
            IAM_TOKEN_URL,
            data={
                "grant_type": "urn:ibm:params:oauth:grant-type:apikey",
                "apikey": settings.ibm_api_key,
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        resp.raise_for_status()
        return resp.json()["access_token"]


async def _call_ibm_granite(
    prompt: str,
    max_new_tokens: int,
    temperature: float,
    system_prompt: str,
) -> dict:
    """Call IBM watsonx.ai Granite inference endpoint."""
    full_prompt = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt
    token = await _get_iam_token()
    payload = {
        "model_id": settings.ibm_granite_model_id,
        "input": full_prompt,
        "parameters": {
            "decoding_method": "sample",
            "max_new_tokens": max_new_tokens,
            "temperature": temperature,
            "top_p": 0.9,
            "repetition_penalty": 1.1,
        },
        "project_id": settings.ibm_project_id,
    }
    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.post(
            IBM_INFERENCE_URL,
            json=payload,
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            },
        )
        resp.raise_for_status()
        text = resp.json()["results"][0]["generated_text"].strip()
        return {
            "text": text,
            "source": "ibm_granite",
            "model": settings.ibm_granite_model_id,
            "data_label": "AI",
        }


# ── Public interface ──────────────────────────────────────────────────────────

async def call_granite(
    prompt: str,
    max_new_tokens: int = 600,
    temperature: float = 0.4,
    system_prompt: str = "",
) -> dict:
    """
    Send a prompt to the best available LLM and return the response.

    Priority: Groq → IBM Granite → demo fallback.

    Returns:
        {
          "text": str,
          "source": "groq" | "ibm_granite" | "demo_fallback" | "error_fallback",
          "model": str,
          "data_label": "AI"
        }
    """
    # 1. Try Groq first
    groq_key = settings.groq_api_key
    if groq_key and groq_key not in ("", "your-groq-api-key-here"):
        try:
            return await _call_groq(prompt, max_new_tokens, temperature, system_prompt)
        except Exception:
            pass  # fall through to IBM Granite

    # 2. Try IBM Granite
    ibm_key = settings.ibm_api_key
    if ibm_key and ibm_key not in ("", "your-ibm-api-key-here"):
        try:
            return await _call_ibm_granite(prompt, max_new_tokens, temperature, system_prompt)
        except Exception:
            return {
                "text": (
                    "[LLM unavailable — demo mode active]\n\n"
                    "Both Groq and IBM Granite are currently unreachable. "
                    "Check your API keys in backend/.env."
                ),
                "source": "error_fallback",
                "model": settings.ibm_granite_model_id,
                "data_label": "AI",
                "error": "All LLM backends failed.",
            }

    # 3. Demo fallback
    return _demo_fallback(prompt)


def _demo_fallback(prompt: str) -> dict:
    """
    Returns a structured demo response when no LLM credentials are configured.
    Clearly marked as demo — never presented as a real AI output.
    """
    return {
        "text": (
            "🤖 [DEMO MODE — No LLM configured]\n\n"
            "This response would be generated by an LLM in production. "
            "The platform supports:\n"
            "• Groq (llama-3.3-70b-versatile) — set GROQ_API_KEY in backend/.env\n"
            "• IBM Granite (watsonx.ai) — set IBM_API_KEY + IBM_PROJECT_ID in backend/.env\n\n"
            "Features powered by AI:\n"
            "• Natural-language itinerary explanations\n"
            "• Eco-assistant conversations in English, Hindi & Gujarati\n"
            "• Authority dashboard summaries\n"
            "• Recommendation reasoning"
        ),
        "source": "demo_fallback",
        "model": "none",
        "data_label": "AI",
    }
