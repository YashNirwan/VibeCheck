# VibeCheck

**AI-curated, API-validated soundtracks for any scene, book, or feeling.**

[![Live Demo](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://vibecheck.streamlit.app)
![Python](https://img.shields.io/badge/Python-3.11-blue?logo=python&logoColor=white)
![Groq](https://img.shields.io/badge/LLM-Llama%203.3%2070B%20via%20Groq-orange)
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

---

## Stack

| Layer | Technology |
|---|---|
| UI | Streamlit |
| LLM | Llama 3.3 70B via Groq Cloud API |
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
