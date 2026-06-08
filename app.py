import streamlit as st
from groq import Groq
from ytmusicapi import YTMusic
import json
import html
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from difflib import SequenceMatcher

# ── CONFIG ────────────────────────────────────────────────────────────────────
st.set_page_config(page_title="VibeCheck", page_icon="🎬", layout="wide")

try:
    GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
except Exception:
    st.error("🚨 GROQ_API_KEY not found. Set it in Streamlit Secrets.")
    st.stop()

MAX_MEMORY      = 5
MATCH_THRESHOLD = 0.40
MAX_WORKERS     = 10
MAX_INPUT_LEN   = 800

EXAMPLE_PROMPTS = [
    "The Road by Cormac McCarthy",
    "A heist going wrong at 3am",
    "Blade Runner 2049 — rain on neon streets",
    "Falling in love in a foreign city",
    "The last day of summer, 1994",
]

# ── CACHED RESOURCES ──────────────────────────────────────────────────────────
@st.cache_resource
def get_ytmusic():
    return YTMusic()

@st.cache_resource
def get_groq_client():
    return Groq(api_key=GROQ_API_KEY)

# ── SESSION STATE ─────────────────────────────────────────────────────────────
_defaults = {
    "memory":         [],
    "track_feedback": {},
    "current_tracks": [],
    "current_vision": "",
    "skipped_tracks": [],
    "input_text":     "",
}
for _k, _v in _defaults.items():
    if _k not in st.session_state:
        st.session_state[_k] = _v

# ── STYLING ───────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;800&display=swap');

.stApp { background-color: #08090C; color: #DDE1EE; font-family: 'Inter', sans-serif; }

h1 {
    font-family: 'Inter', sans-serif;
    font-weight: 800;
    letter-spacing: -3px;
    font-size: 4.2rem !important;
    background: linear-gradient(135deg, #ffffff 0%, #7779a0 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    padding-bottom: 2px;
    margin-bottom: 0 !important;
    line-height: 1 !important;
}

.tagline { color: #555; font-size: 0.88rem; letter-spacing: 0.8px; margin-bottom: 28px; margin-top: 4px; }

.stTextInput > div > div > input {
    background-color: #10121A !important;
    color: #DDE1EE !important;
    border-radius: 10px !important;
    border: 1px solid #1E2130 !important;
    font-size: 0.95rem !important;
}
.stTextInput > div > div > input:focus { border-color: #6366f1 !important; }

div[data-testid="stTextInput"] label,
div[data-testid="stSlider"] label,
div[data-testid="stToggle"] label { color: #666 !important; font-size: 0.78rem !important; }

.stButton > button {
    background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%) !important;
    color: white !important; border: none !important;
    font-weight: 700 !important; border-radius: 10px !important;
    letter-spacing: 1.2px !important; transition: opacity 0.2s !important;
}
.stButton > button:hover { opacity: 0.82 !important; }
.stButton > button[kind="secondary"] {
    background: #10121A !important; border: 1px solid #1E2130 !important;
    color: #666 !important; font-weight: 500 !important; letter-spacing: 0.4px !important;
}
.stButton > button[kind="secondary"]:hover { border-color: #6366f1 !important; color: #DDE1EE !important; }

.track-card {
    background: #10121A; border: 1px solid #181C2A;
    border-radius: 14px; overflow: hidden;
    transition: transform 0.2s, border-color 0.2s, box-shadow 0.2s;
    margin-bottom: 4px;
}
.track-card:hover {
    transform: translateY(-3px); border-color: #6366f1;
    box-shadow: 0 8px 32px rgba(99,102,241,0.15);
}
.track-img { width: 100%; aspect-ratio: 1; object-fit: cover; display: block; }
.track-img-placeholder {
    width: 100%; aspect-ratio: 1; background: #181C2A;
    display: flex; align-items: center; justify-content: center; font-size: 2.5rem;
}
.track-info { padding: 12px 14px 10px; }
.track-num  { color: #2A2E42; font-size: 0.63rem; font-weight: 700; letter-spacing: 1.5px; margin-bottom: 6px; }
.era-badge  {
    display: inline-block; background: #181C2A; color: #6366f1;
    border: 1px solid #252840; border-radius: 20px;
    font-size: 0.62rem; font-weight: 700; padding: 2px 8px;
    letter-spacing: 0.8px; margin-bottom: 7px; text-transform: uppercase;
}
.track-title  { font-weight: 700; font-size: 0.88rem; line-height: 1.3; color: #DDE1EE; margin-bottom: 2px; }
.track-artist { color: #555; font-size: 0.78rem; margin-bottom: 7px; }
.track-reason { color: #3E4260; font-size: 0.7rem; line-height: 1.5; font-style: italic; }

.vision-box {
    border-left: 3px solid #6366f1; padding: 18px 22px;
    background: #10121A; border-radius: 0 12px 12px 0;
    font-size: 0.9rem; line-height: 1.75; color: #8A8FAA; margin-bottom: 20px;
}

.playlist-header {
    background: #10121A; border: 1px solid #181C2A;
    border-radius: 12px; padding: 14px 22px;
    display: flex; gap: 32px; align-items: center; margin-bottom: 20px;
}
.ph-val { font-size: 1.3rem; font-weight: 800; color: #DDE1EE; line-height: 1; }
.ph-lbl { font-size: 0.6rem; color: #444; letter-spacing: 1.2px; font-weight: 700; text-transform: uppercase; margin-top: 3px; }

.chip-btn .stButton > button {
    background: #10121A !important; border: 1px solid #1A1D2A !important;
    color: #555 !important; font-weight: 400 !important;
    font-size: 0.76rem !important; padding: 5px 10px !important;
    border-radius: 20px !important; letter-spacing: 0.2px !important;
}
.chip-btn .stButton > button:hover { border-color: #6366f1 !important; color: #DDE1EE !important; }

.skipped-notice {
    background: #120E0A; border: 1px solid #2A1A0A;
    border-radius: 8px; padding: 9px 14px;
    font-size: 0.76rem; color: #7A5530; margin-top: 14px;
}

.utility-box {
    background: #10121A; padding: 12px 14px; border-radius: 10px;
    margin-bottom: 8px; border: 1px solid #181C2A;
    font-size: 0.8rem; line-height: 1.5;
}

div[data-testid="stHorizontalBlock"] { gap: 10px; }
</style>
""", unsafe_allow_html=True)

# ── HELPERS ───────────────────────────────────────────────────────────────────
def _similarity(a: str, b: str) -> float:
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()

def _extract_year(era: str) -> int:
    m = re.search(r'\d{4}', era)
    if m:
        return int(m.group())
    m = re.search(r'(\d{2,3})s', era)
    if m:
        v = int(m.group(1))
        return (1900 + v) if v < 100 else v
    return 2000

def search_single_track(track_data: dict, yt: YTMusic) -> dict | None:
    """Try primary query then fallbacks; return enriched dict or None."""
    queries = [track_data.get("primary_query", "")] + track_data.get("fallback_queries", [])
    for q in queries:
        if not q:
            continue
        try:
            results = yt.search(q, filter="songs")
            if not results:
                continue
            top             = results[0]
            returned_artist = (top.get("artists") or [{}])[0].get("name", "")
            returned_title  = top.get("title", "")
            parts           = q.split("::")
            expected_artist = parts[0].strip() if len(parts) > 0 else ""
            expected_title  = parts[1].strip() if len(parts) > 1 else q
            if (_similarity(returned_artist, expected_artist) >= MATCH_THRESHOLD or
                    _similarity(returned_title, expected_title)  >= MATCH_THRESHOLD):
                return {
                    "title":     returned_title,
                    "artist":    returned_artist,
                    "videoId":   top["videoId"],
                    "thumbnail": (top.get("thumbnails") or [{}])[-1].get("url"),
                    "era":       track_data.get("era", ""),
                    "reason":    track_data.get("reason", ""),
                }
        except Exception:
            continue
    return None

def render_track_card(track: dict, idx: int) -> str:
    title  = html.escape(track.get("title",  ""))
    artist = html.escape(track.get("artist", ""))
    era    = html.escape(track.get("era",    ""))
    reason = html.escape(track.get("reason", ""))
    vid    = track["videoId"]
    thumb  = track.get("thumbnail") or ""

    img_block    = (f'<img class="track-img" src="{thumb}" alt="{title}">'
                    if thumb else '<div class="track-img-placeholder">♪</div>')
    era_block    = f'<span class="era-badge">{era}</span><br>' if era    else ""
    reason_block = f'<p class="track-reason">{reason}</p>'    if reason else ""

    return f"""
<div class="track-card">
  <a href="https://music.youtube.com/watch?v={vid}" target="_blank" style="text-decoration:none;">
    {img_block}
  </a>
  <div class="track-info">
    <div class="track-num">TRACK {idx+1:02d}</div>
    {era_block}
    <div class="track-title">{title}</div>
    <div class="track-artist">{artist}</div>
    {reason_block}
  </div>
</div>"""

# ── SIDEBAR ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### System")
    st.markdown("""
<div class='utility-box'>
<b>Truth Filter</b><br>
<small>Every track is cross-referenced against YouTube Music with confidence scoring.
Hallucinated songs are caught and replaced via fallback queries.</small>
</div>
<div class='utility-box'>
<b>Smart Platter</b><br>
<small>Forced era mixing — period-accurate anchors + modern philosophical matches
+ bridge tracks connecting the eras.</small>
</div>
<div class='utility-box'>
<b>Feedback Loop</b><br>
<small>👍/👎 each track, then hit <b>Tweak Mix</b>. The AI adjusts the next
generation based on your signals.</small>
</div>
<div class='utility-box'>
<b>Zero-Friction Queue</b><br>
<small>One "Play All" link aggregates every validated Video ID.</small>
</div>
""", unsafe_allow_html=True)

    if st.session_state.memory:
        st.markdown("---")
        st.markdown("**Session Memory**")
        for _m in st.session_state.memory:
            st.markdown(f"<small style='color:#444'>• {html.escape(_m)}</small>",
                        unsafe_allow_html=True)
        if st.button("Clear Memory", type="secondary"):
            st.session_state.memory = []
            st.rerun()

# ── MAIN ──────────────────────────────────────────────────────────────────────
st.markdown("<h1>VibeCheck</h1>", unsafe_allow_html=True)
st.markdown(
    "<p class='tagline'>AI-curated, API-validated soundtracks for any scene, book, or feeling.</p>",
    unsafe_allow_html=True,
)

# Example prompt chips
st.markdown("<small style='color:#333;letter-spacing:1px;font-weight:700'>TRY</small>",
            unsafe_allow_html=True)
chip_cols = st.columns(len(EXAMPLE_PROMPTS))
for _i, _prompt in enumerate(EXAMPLE_PROMPTS):
    with chip_cols[_i]:
        st.markdown('<div class="chip-btn">', unsafe_allow_html=True)
        if st.button(_prompt, key=f"chip_{_i}", use_container_width=True):
            st.session_state.input_text = _prompt
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

st.divider()

col_in, col_opt = st.columns([3, 1])
with col_in:
    user_input = st.text_input(
        "Scene, book title, or feeling:",
        key="input_text",
        placeholder="e.g.  'The Age of Reason' by Sartre  –or–  'A tense dinner turning violent'",
        max_chars=MAX_INPUT_LEN,
    )
with col_opt:
    reading_mode    = st.toggle("Reading Mode", value=False,
                                help="Instrumental/Ambient only — no lyrics.")
    num_songs       = st.slider("Tracks", 3, 40, 12)
    exclude_artists = st.text_input("Exclude artists", placeholder="e.g. Drake, Coldplay",
                                    help="Comma-separated artists to avoid.")

with st.expander("Pro tips"):
    st.markdown("""
- **Detail helps:** paste a full paragraph — lighting, weather, emotion all sharpen the mix.
- **Contrast works:** *"A violent scene with peaceful classical music"* gives very specific results.
- **Specifics beat vibes:** *"Flickering neon in rain"* pulls different songs than *"Cyberpunk City."*
- **Feedback loop:** 👍/👎 tracks, then hit **Tweak Mix** for a refined second pass.
""")

btn_col1, btn_col2 = st.columns([2, 1])
with btn_col1:
    generate = st.button("CURATE MIX", use_container_width=True)
with btn_col2:
    tweak = st.button(
        "TWEAK MIX", use_container_width=True,
        disabled=not bool(st.session_state.current_tracks),
        help="Refine the current mix using your 👍/👎 feedback.",
        type="secondary",
    )

# ── GENERATION ────────────────────────────────────────────────────────────────
if generate or tweak:
    if not user_input.strip():
        st.warning("Please describe a scene, book, or feeling.")
    else:
        yt = get_ytmusic()

        lessons = "\n".join(f"- {l}" for l in st.session_state.memory[-MAX_MEMORY:])

        liked_titles    = [t["title"] for t in st.session_state.current_tracks
                           if st.session_state.track_feedback.get(t["videoId"]) == "liked"]
        disliked_titles = [t["title"] for t in st.session_state.current_tracks
                           if st.session_state.track_feedback.get(t["videoId"]) == "disliked"]

        feedback_ctx = ""
        if tweak and (liked_titles or disliked_titles):
            feedback_ctx = (
                f"\nUSER FEEDBACK ON LAST MIX:"
                f"\n  Liked:    {', '.join(liked_titles)    or 'none'}"
                f"\n  Disliked: {', '.join(disliked_titles) or 'none'}"
                "\nLean into what was liked; avoid what was disliked."
            )

        exclude_ctx = (
            f"\nEXCLUDE THESE ARTISTS (do not include them): {exclude_artists.strip()}"
            if exclude_artists.strip() else ""
        )
        music_type = (
            "INSTRUMENTAL / AMBIENT / SCORE ONLY — absolutely no lyrics"
            if reading_mode else
            "ANY — lyrics allowed when thematically justified"
        )

        system_prompt = (
            "You are a world-renowned Cinema Music Supervisor celebrated for 'anachronistically perfect' choices.\n"
            "You think in emotional truth and philosophy first, genre second.\n"
            "Your mixes feel inevitable in retrospect.\n"
            "Return only valid JSON — no text outside the JSON object."
        )

        user_prompt = f"""INPUT: "{user_input}"
MODE: {music_type}
COUNT: {num_songs} tracks.
SESSION LESSONS: {lessons or "none yet"}
{feedback_ctx}
{exclude_ctx}

MIXING RULES:
1. EMOTIONAL TRUTH is the highest priority — does it *feel* right?
2. SMART PLATTER — deliberately mix eras:
   • 1-2 period-accurate anchor tracks (to ground the scene).
   • 2-3 modern tracks sharing the same philosophy/emotion.
   • 1-2 bridge tracks (Jazz Noir, Dark Ambient, Post-Rock) connecting the eras.
3. Per track: provide 2 fallback queries in case the primary is unavailable.
4. Per track: one sentence explaining the emotional/philosophical connection to the input.
5. If READING MODE: still mix Classical + Modern Ambient/Drone.

Return EXACTLY this JSON — no extra keys:
{{
  "vision": "2-3 sentences: what emotional arc does this playlist trace? What connects the earliest track to the newest?",
  "tracks": [
    {{
      "primary_query":    "Artist Name :: Song Title :: Year",
      "fallback_queries": ["Artist Name :: Alt Song :: Year", "Artist Name :: Alt Song 2 :: Year"],
      "reason": "One sentence: why this specific track in this specific mix.",
      "era":    "e.g. 1960s  or  2019"
    }}
  ],
  "lesson": "One takeaway about this specific vibe for future sessions."
}}"""

        progress_slot = st.empty()
        with progress_slot:
            prog = st.progress(0, text="Synthesizing mix with AI...")

        # LLM call
        try:
            completion = get_groq_client().chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user",   "content": user_prompt},
                ],
                response_format={"type": "json_object"},
            )
            data = json.loads(completion.choices[0].message.content)
        except json.JSONDecodeError as e:
            progress_slot.empty()
            st.error(f"AI returned malformed JSON — try again. ({e})")
            st.stop()
        except Exception as e:
            progress_slot.empty()
            st.error(f"AI request failed: {e}")
            st.stop()

        if "lesson" in data:
            st.session_state.memory.append(data["lesson"])
            st.session_state.memory = st.session_state.memory[-MAX_MEMORY:]

        track_data = data.get("tracks", [])
        prog.progress(0.15, text=f"Validating {len(track_data)} tracks against YouTube Music...")

        # Parallel track search
        resolved: dict[int, dict] = {}
        skipped:  list[str]       = []

        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            futures = {
                executor.submit(search_single_track, td, yt): i
                for i, td in enumerate(track_data)
            }
            done = 0
            for future in as_completed(futures):
                i      = futures[future]
                result = future.result()
                done  += 1
                prog.progress(
                    0.15 + 0.80 * (done / len(futures)),
                    text=f"Validated {done}/{len(futures)} tracks...",
                )
                if result:
                    resolved[i] = result
                else:
                    skipped.append(track_data[i].get("primary_query", f"Track {i+1}"))

        progress_slot.empty()

        st.session_state.current_tracks  = [resolved[i] for i in sorted(resolved)]
        st.session_state.current_vision  = data.get("vision", "")
        st.session_state.skipped_tracks  = skipped
        st.session_state.track_feedback  = {}

# ── RESULTS ───────────────────────────────────────────────────────────────────
tracks = st.session_state.current_tracks
vision = st.session_state.current_vision

if tracks:
    st.markdown("### Director's Vision")
    st.markdown(
        f"<div class='vision-box'>{html.escape(vision)}</div>",
        unsafe_allow_html=True,
    )

    # Playlist header stats
    eras      = [t.get("era", "") for t in tracks if t.get("era")]
    era_years = sorted(set(_extract_year(e) for e in eras)) if eras else []
    if len(era_years) >= 2:
        era_display = f"{era_years[0]}s → {era_years[-1]}s"
    elif era_years:
        era_display = str(era_years[0])
    else:
        era_display = "—"

    st.markdown(f"""
<div class='playlist-header'>
  <div><div class='ph-val'>{len(tracks)}</div><div class='ph-lbl'>Tracks</div></div>
  <div><div class='ph-val' style='font-size:1rem'>{era_display}</div><div class='ph-lbl'>Era Span</div></div>
  <div><div class='ph-val'>{len(set(era_years))}</div><div class='ph-lbl'>Eras Mixed</div></div>
  <div><div class='ph-val'>{len(st.session_state.skipped_tracks)}</div><div class='ph-lbl'>Filtered Out</div></div>
</div>""", unsafe_allow_html=True)

    # Track grid
    cols = st.columns(4)
    for idx, track in enumerate(tracks):
        with cols[idx % 4]:
            st.markdown(render_track_card(track, idx), unsafe_allow_html=True)

            vid = track["videoId"]
            fb  = st.session_state.track_feedback.get(vid, "")
            b1, b2, b3 = st.columns(3)

            if b1.button("✓ Liked" if fb == "liked"    else "👍",
                         key=f"like_{vid}", use_container_width=True, type="secondary"):
                st.session_state.track_feedback[vid] = "" if fb == "liked" else "liked"
                st.rerun()
            if b2.button("✓ Nope"  if fb == "disliked" else "👎",
                         key=f"dislike_{vid}", use_container_width=True, type="secondary"):
                st.session_state.track_feedback[vid] = "" if fb == "disliked" else "disliked"
                st.rerun()
            if b3.button("✕", key=f"remove_{vid}", use_container_width=True,
                         help="Remove this track", type="secondary"):
                st.session_state.current_tracks = [
                    t for t in st.session_state.current_tracks if t["videoId"] != vid
                ]
                st.rerun()

    # Skipped notice
    if st.session_state.skipped_tracks:
        s      = st.session_state.skipped_tracks
        sample = ", ".join(html.escape(x) for x in s[:4])
        more   = f" +{len(s)-4} more" if len(s) > 4 else ""
        st.markdown(
            f"<div class='skipped-notice'>⚠ {len(s)} track(s) couldn't be verified and were filtered out:"
            f" {sample}{more}</div>",
            unsafe_allow_html=True,
        )

    # Play All
    video_ids = [t["videoId"] for t in tracks]
    if video_ids:
        url = f"https://www.youtube.com/watch_videos?video_ids={','.join(video_ids)}"
        st.markdown(f"""
<a href="{url}" target="_blank">
  <button style="background:linear-gradient(135deg,#6366f1,#8b5cf6);color:white;width:100%;
    padding:18px;border:none;border-radius:12px;cursor:pointer;font-size:1.05rem;font-weight:700;
    letter-spacing:2px;margin-top:20px;display:block;">
    PLAY FULL MIX &nbsp;({len(video_ids)} TRACKS)
  </button>
</a>""", unsafe_allow_html=True)
