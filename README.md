# VibeCheck: AI Music Supervisor

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://share.streamlit.io/)
![Python](https://img.shields.io/badge/Python-3.9%2B-blue)
![Vibe Coded](https://img.shields.io/badge/Status-Vibe%20Coded-purple)

**VibeCheck** is an intelligent soundtrack generator that translates abstract concepts (book titles, scene descriptions, emotions) into playable, cross-era playlists.

Unlike standard playlist generators, VibeCheck uses a **two-step verification system**: it employs an LLM (Llama 3 via Groq) for creative curation and the YouTube Music API for sonic validation, ensuring zero hallucinations.

---

## Key Features

* **Sub-Second Inference:** Leverages **Groq's LPU** (Linear Processing Unit) architecture for near-instant AI responses.
* **The Truth Filter:** Solves the "AI Hallucination" problem by cross-referencing every generated song against the **YouTube Music API** to ensure playability.
* **Context-Aware Curation:** Understands nuance (e.g., *"A 19th-century duel with 2024 techno"*).
* **Zero-Friction UX:** Auto-aggregates video IDs to generate a single "Play All" deep link, removing manual queueing.

---

## Tech Stack

* **Frontend:** Streamlit (Python-based UI).
* **Intelligence:** Llama 3.3 (70B) via Groq Cloud API.
* **Data Validation:** `ytmusicapi` (Unofficial YouTube Music API).
* **Deployment:** Streamlit Community Cloud (CI/CD via GitHub).

---

## Engineering Journey & Learnings

This project was **"Vibe Coded"**—built with a focus on rapid iteration, user-centric design, and AI-assisted coding to bridge the gap between idea and deployment instantly.

**Key Technical Takeaways:**
1.  **Mitigating LLM Hallucinations:** I learned that LLMs often invent song titles. I built a validation layer that treats the LLM output as a *suggestion* and the Music API as the *truth*, filtering out non-existent tracks before they reach the UI.
2.  **Prompt Engineering for Structure:** Designed a JSON-enforced system prompt to ensure the AI returns structured data (Vision, Queries, Lessons) rather than unstructured text, allowing for clean UI rendering.
3.  **API Latency Management:** Optimized the search loop to handle 40+ API calls asynchronously while providing user feedback via Streamlit spinners.
4.  **State Management:** Implemented `st.session_state` to give the AI "memory," allowing it to learn from previous generations in the same session.

---

## How to Run Locally

1. **Clone the repo**
   ```bash
   git clone [https://github.com/YOUR_USERNAME/vibecheck.git](https://github.com/YOUR_USERNAME/vibecheck.git)
   cd vibecheck