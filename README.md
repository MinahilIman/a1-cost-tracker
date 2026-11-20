
# Two Provider Cost Tracker (Assignment 1)

A Python application built to query two separate Large Language Model (LLM) providers (Google Gemini and Groq) simultaneously, extract exact token usage metadata directly from API responses, calculate total request costs based on per-million token pricing, display side-by-side comparative terminal tables, and log output metrics into `results.json`.


## Project Architecture & Directory Structure

```text
ai-cost-tracker/
├── .env                 # API keys & model configuration (Ignored by Git)
├── .env.example         # Template for environment variables (Committed)
├── .gitignore           # Ensures secrets are not uploaded
├── pyproject.toml       # Dependencies managed by uv
├── tracker.py           # Core multi-provider cost tracking script
├── results.json         # Output data generated after each execution
└── README.md            # Comprehensive project documentation
```


## Setup & Secrets Management

1. **Clone the repository and enter the directory:**

   ```bash
   git clone <your-repository-url>
   cd ai-cost-tracker
   ```

2. **Configure environment variables:**

   Copy the `.env.example` file to `.env`:

   ```bash
   cp .env.example .env
   ```

3. **Add API credentials to `.env`:**

   ```env
   GEMINI_API_KEY=your_gemini_api_key_here
   GEMINI_MODEL=gemini-3.5-flash-lite
   GEMINI_INPUT_PRICE_PER_M=0.30
   GEMINI_OUTPUT_PRICE_PER_M=2.50

   GROQ_API_KEY=your_groq_api_key_here
   GROQ_MODEL=openai/gpt-oss-120b
   GROQ_INPUT_PRICE_PER_M=0.30
   GROQ_OUTPUT_PRICE_PER_M=0.40
   ```

4. **Secrets Verification:**

   The `.gitignore` file strictly excludes `.env` to prevent sensitive API keys from being exposed in public repositories.

---

## How to Run

Execute the tracker script using `uv` by passing your prompt string directly as a command-line argument:

```bash
uv run tracker.py "Explain what a token is in one sentence"
```


## Comparative Test Runs & Multi-Prompt Analysis

### Test Prompt 1: Short Definition

**Command:**

```bash
uv run tracker.py "Explain what a token is in one sentence"
```

**Terminal Output:**

```text
--- gemini (gemini-3.5-flash-lite) ---
In the context of AI and language models, a token is a fundamental unit of text—ranging from a fraction of a word to a full word—that the model reads, processes, and generates.

--- groq (openai/gpt-oss-120b) ---
A token is a discrete unit of text—such as a word, sub-word fragment, or character—used by language models to represent and process language.

==============================================================
Provider       Input    Output   Seconds      Cost (USD)
--------------------------------------------------------------
gemini             9        40     13.92        0.000103
groq              79        71      0.78        0.000054
==============================================================
Saved results.json
```

**Observation:** Groq achieved sub-second latency (0.78s) compared to Gemini (13.92s). Gemini's tokenizer evaluated the input string as 9 tokens, whereas Groq counted 79 input tokens due to provider tokenization differences.


### Test Prompt 2: Code Generation

**Command:**

```bash
uv run tracker.py "Write a Python function to check if a string is a palindrome. Include docstrings."
```

**Terminal Output:**

```text
==============================================================
Provider       Input    Output   Seconds      Cost (USD)
--------------------------------------------------------------
gemini            18       515      7.57        0.001293
groq              88       518      1.69        0.000324
==============================================================
Saved results.json
```

**Observation:** Both models returned complete Python functions with docstrings and type hinting (~515–518 output tokens). Groq ran 4.4x faster (1.69s vs 7.57s) and yielded a lower request cost ($0.000324 vs $0.001293).


### Test Prompt 3: Technical Comparison (Structured)

**Command:**

```bash
uv run tracker.py "Explain the difference between REST API and GraphQL in 3 bullet points."
```

**Terminal Output:**

```text
==============================================================
Provider       Input    Output   Seconds      Cost (USD)
--------------------------------------------------------------
gemini            15       171       5.0        0.000432
groq              86       266       1.2        0.000172
==============================================================
Saved results.json
```

**Observation:** Gemini generated concise top-level bullet points (171 output tokens), while Groq generated a more detailed response with nested sub-bullets (266 output tokens). Groq maintained lower execution time (1.2s).


### Test Prompt 4: Creative Writing

**Command:**

```bash
uv run tracker.py "Give me a creative 2-sentence story about an AI learning to feel emotions."
```

**Terminal Output:**

```text
==============================================================
Provider       Input    Output   Seconds      Cost (USD)
--------------------------------------------------------------
gemini            18        61      1.21        0.000158
groq              88       121      0.80        0.000086
==============================================================
Saved results.json
```

**Observation:** Gemini provided a concise 2-sentence paragraph (61 tokens in 1.21s). Groq delivered a descriptive two-sentence story (121 tokens in 0.80s).


## Core Technical Learnings

1. **Tokenization Discrepancies Across Providers:** The exact same prompt string produces significantly different input token counts across providers (e.g., 9–18 tokens on Gemini vs 79–88 tokens on Groq). This confirms why token counts must always be read directly from API metadata rather than estimated by counting words or characters.

2. **Speed vs. Cost Trade-offs:** Groq consistently provided sub-second or near-instant execution across prompts, making it very effective for low-latency tasks. Total cost relies heavily on output length because output tokens cost significantly more per million than input tokens.

3. **Resilience & Defensive Coding:** Provider rate limits (e.g., HTTP `429` quota limits and HTTP `504` deadlines) demonstrate the importance of error handling, fallback logic, retry attempts, and separate configurations in `.env` to prevent one failing provider from breaking the application.
