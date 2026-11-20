"""Send one prompt to Gemini and Groq, then compare reply, tokens, time and cost.

Run:  uv run tracker.py "your prompt"
"""

import json
import os
import sys
import time

from dotenv import load_dotenv
load_dotenv(override=True)
from google import genai
from google.genai import types
from groq import Groq

# Read the .env file so os.getenv() can see our keys and settings.
load_dotenv()

# Everything we need from .env. If any is missing we stop with a clear message.
REQUIRED_SETTINGS = [
    "GEMINI_API_KEY",
    "GEMINI_MODEL",
    "GEMINI_INPUT_PRICE_PER_M",
    "GEMINI_OUTPUT_PRICE_PER_M",
    "GROQ_API_KEY",
    "GROQ_MODEL",
    "GROQ_INPUT_PRICE_PER_M",
    "GROQ_OUTPUT_PRICE_PER_M",
]


def check_settings():
    """Stop the program with a friendly message if anything is missing in .env."""
    missing = [name for name in REQUIRED_SETTINGS if not os.getenv(name)]
    if missing:
        print("Missing settings in your .env file:")
        for name in missing:
            print(f"  - {name}")
        print("Copy .env.example to .env and fill in the real values.")
        sys.exit(1)


def calculate_cost(input_tokens, output_tokens, input_price_per_m, output_price_per_m):
    """Prices are per 1,000,000 tokens, so divide by 1,000,000."""
    input_cost = input_tokens * input_price_per_m / 1_000_000
    output_cost = output_tokens * output_price_per_m / 1_000_000
    return input_cost + output_cost


def ask_gemini(prompt):
    """Send the prompt to Gemini and return the reply and token counts."""
    # timeout in milliseconds: 60000 ms = 60 seconds
    client = genai.Client(
        api_key=os.getenv("GEMINI_API_KEY"),
        http_options=types.HttpOptions(timeout=60000),
    )
    model = os.getenv("GEMINI_MODEL")
    input_price = float(os.getenv("GEMINI_INPUT_PRICE_PER_M"))
    output_price = float(os.getenv("GEMINI_OUTPUT_PRICE_PER_M"))

    start = time.time()
    response = client.models.generate_content(model=model, contents=prompt)
    seconds = time.time() - start

    # Token counts come from the API's usage data, never estimated.
    usage = response.usage_metadata
    input_tokens = usage.prompt_token_count or 0
    # Gemini bills "thinking" tokens as output, so we add them in.
    output_tokens = (usage.candidates_token_count or 0) + (usage.thoughts_token_count or 0)

    return {
        "provider": "gemini",
        "model": model,
        "reply": response.text,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "input_price_per_m": input_price,
        "output_price_per_m": output_price,
        "cost_usd": calculate_cost(input_tokens, output_tokens, input_price, output_price),
        "seconds": round(seconds, 2),
    }

def ask_groq(prompt):
    """Send the prompt to Groq and return the reply and token counts."""
    client = Groq(api_key=os.getenv("GROQ_API_KEY"), timeout=30)
    model = os.getenv("GROQ_MODEL")
    input_price = float(os.getenv("GROQ_INPUT_PRICE_PER_M"))
    output_price = float(os.getenv("GROQ_OUTPUT_PRICE_PER_M"))

    start = time.time()
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
    )
    seconds = time.time() - start

    usage = response.usage
    input_tokens = usage.prompt_tokens
    output_tokens = usage.completion_tokens

    return {
        "provider": "groq",
        "model": model,
        "reply": response.choices[0].message.content,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "input_price_per_m": input_price,
        "output_price_per_m": output_price,
        "cost_usd": calculate_cost(input_tokens, output_tokens, input_price, output_price),
        "seconds": round(seconds, 2),
    }


def print_table(results):
    """Print a simple table: provider, input tokens, output tokens, seconds, cost."""
    print("\n" + "=" * 62)
    print(f"{'Provider':<10}{'Input':>10}{'Output':>10}{'Seconds':>10}{'Cost (USD)':>16}")
    print("-" * 62)
    for r in results:
        print(
            f"{r['provider']:<10}{r['input_tokens']:>10}{r['output_tokens']:>10}"
            f"{r['seconds']:>10}{r['cost_usd']:>16.6f}"
        )
    print("=" * 62)


def with_retries(ask, prompt, tries=3):
    # Try a provider a few times, because servers are sometimes busy.
    for attempt in range(1, tries + 1):
        try:
            return ask(prompt)
        except Exception:
            if attempt == tries:
                raise
            print(f"[{ask.__name__}] attempt {attempt} failed, retrying in 5 seconds...")
            time.sleep(5)


def main():
    # The prompt is whatever you type after tracker.py
    if len(sys.argv) < 2:
        print('Usage: uv run tracker.py "your prompt"')
        sys.exit(1)
    prompt = sys.argv[1]

    check_settings()

    results = []
    for ask in (ask_gemini, ask_groq):
        try:
            result = with_retries(ask, prompt)
        except Exception as error:
            # One provider failing should not stop the other.
            print(f"\n[{ask.__name__}] failed: {error}")
            continue
        print(f"\n--- {result['provider']} ({result['model']}) ---")
        print(result["reply"])
        results.append(result)

    if results:
        print_table(results)
        with open("results.json", "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        print("Saved results.json")


if __name__ == "__main__":
    main()