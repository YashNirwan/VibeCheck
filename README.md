# VibeCheck

**AI-curated, API-validated soundtracks for any scene, book, or feeling.**

[![Live Demo](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://vibecheck.streamlit.app)
![Python](https://img.shields.io/badge/Python-3.11-blue?logo=python&logoColor=white)
![Groq](https://img.shields.io/badge/LLM-gpt--oss--120b%20via%20Groq-orange)
![License](https://img.shields.io/badge/License-MIT-green)

---

![VibeCheck screenshot](https://raw.githubusercontent.com/YashNirwan/VibeCheck/main/assets/screenshot.png)

---

## What it does

Give VibeCheck a book title, scene description, or feeling — it generates a cross-era playlist, verifies every track exists on YouTube Music, and gives you a single "Play All" link.

The key distinction from other AI playlist tools: **the LLM is treated as a suggestion engine, not a source of truth.** Every generated song title is cross-referenced against the YouTube Music API before it reaches the UI. Hallucinated tracks are caught and replaced via fallback queries, not silently shown.

---

## Technical decisions worth noting

**1. Hallucination filter with confidence scoring**  
LLMs routinely invent plausible-sounding song titles. Instead of trusting the model's output directly, I parse each suggested track, search YouTube Music, and compute a string similarity score (SequenceMatcher) between the returned artist/title and the expected values. Tracks below the confidence threshold are retried with fallback queries, then dropped if all fail.

**2. Parallel API validation**  
The original implementation made 40+ `ytmusicapi` calls sequentially — one per track. Replacing the loop with `ThreadPoolExecutor` (10 workers) reduced validation time by ~8–10x for large mixes, with a live progress bar updating as futures resolve.

**3. Structured LLM output via system/user message separation**  
The prompt enforces a strict JSON schema (`primary_query`, `fallback_queries`, `reason`, `era` per track) using Groq's `response_format: json_object`. The system message carries the Music Supervisor persona; the user message carries constraints. This separation keeps the model's output consistent across varied inputs.

**4. Session feedback loop**  
Per-track 👍/👎 signals are stored in `st.session_state` and injected into the next generation prompt as explicit liked/disliked context. The model adjusts its selections without needing a fine-tune or vector store.


**5. Reasoning effort chosen by measurement, with a fallback**  
Model and settings were picked by running VibeCheck's own prompt and validator over the same 8 scenes and checking every track against YouTube Music on both artist *and* title. `gpt-oss-120b` at high reasoning effort scored 97% and always returned the full count; default effort 92%; the newer `qwen3.8-27b` 58%, with most requests rate-limited. High effort costs 30–80 s and ~10k tokens, so a refusal or a run past 50 s falls back to default effort rather than failing the request. The same run found the prompt asked for 12 tracks while its mixing rules capped a mix at 7 — the rules are now proportions of the requested count.
---

## Stack

| Layer | Technology |
|---|---|
| UI | Streamlit |
| LLM | gpt-oss-120b via Groq Cloud API (high reasoning effort, default-effort fallback) |
| Music validation | `ytmusicapi` (YouTube Music) |
| Concurrency | `concurrent.futures.ThreadPoolExecutor` |
| Deployment | Streamlit Community Cloud |

---

## Run locally

```bash
git clone https://github.com/YashNirwan/VibeCheck.git
cd VibeCheck
pip install -r requirements.txt
```

Add your Groq API key to `.streamlit/secrets.toml`:

```toml
GROQ_API_KEY = "your_key_here"
```

```bash
streamlit run app.py
```

Get a free Groq API key at [console.groq.com](https://console.groq.com).
