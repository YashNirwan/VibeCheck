import streamlit as st
from groq import Groq
from ytmusicapi import YTMusic
import json

# --- PAGE CONFIG ---
st.set_page_config(page_title="VibeCheck", page_icon="🎬", layout="wide")

# --- 🔐 SECURITY ---
try:
    GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
except:
    st.error("🚨 API Key not found! Please set it in Streamlit Secrets.")
    st.stop()

# Initialize Memory
if 'memory' not in st.session_state:
    st.session_state.memory = []

# --- UI STYLING (THE UPGRADE) ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');
    
    /* GLOBAL THEME */
    .stApp { background-color: #0E1117; color: white; font-family: 'Inter', sans-serif; }
    
    /* HEADER STYLING */
    h1 {
        font-weight: 800;
        letter-spacing: -2px;
        font-size: 4rem !important;
        background: linear-gradient(to right, #ffffff, #888888);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0px;
    }
    
    /* INPUT FORM STYLING */
    .stTextInput > div > div > input { 
        background-color: #161B22; 
        color: #E6EDF3; 
        border-radius: 12px; 
        border: 1px solid #30363D; 
        padding: 12px;
    }
    .stTextInput > div > div > input:focus {
        border-color: #2575fc;
        box-shadow: 0 0 10px rgba(37, 117, 252, 0.2);
    }
    
    /* BUTTON STYLING */
    .stButton > button, div[data-testid="stFormSubmitButton"] > button {
        background: linear-gradient(90deg, #6a11cb 0%, #2575fc 100%);
        color: white; border: none; padding: 16px; font-weight: 700; border-radius: 12px; width: 100%;
        font-size: 1.1em; letter-spacing: 1px;
        transition: transform 0.1s ease, box-shadow 0.2s ease;
    }
    .stButton > button:hover, div[data-testid="stFormSubmitButton"] > button:hover {
        transform: scale(1.02);
        box-shadow: 0 5px 15px rgba(37, 117, 252, 0.4);
    }

    /* CUSTOM MUSIC CARD (Spotify Style) */
    .music-card {
        background-color: #161B22;
        border: 1px solid #30363D;
        border-radius: 12px;
        padding: 12px;
        margin-bottom: 20px;
        transition: all 0.3s ease;
        height: 100%; /* Ensures equal height in grid */
        cursor: pointer;
        position: relative;
        overflow: hidden;
    }
    .music-card:hover {
        transform: translateY(-5px);
        border-color: #2575fc;
        box-shadow: 0 10px 30px rgba(0,0,0,0.5);
    }
    .card-img {
        width: 100%;
        aspect-ratio: 1/1;
        object-fit: cover;
        border-radius: 8px;
        margin-bottom: 12px;
    }
    .card-title {
        font-weight: 700;
        font-size: 1.1em;
        color: #fff;
        margin-bottom: 4px;
        line-height: 1.2;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }
    .card-artist {
        font-size: 0.9em;
        color: #8b949e;
        margin-bottom: 8px;
    }
    .card-link {
        text-decoration: none;
        color: inherit;
        display: block;
    }
    
    /* UTILITY BOXES */
    .vision-box { border-left: 4px solid #2575fc; padding: 20px; background: #12151C; border-radius: 0 12px 12px 0; font-size: 1.05em; line-height: 1.6; }
    .utility-box { background: #161B22; padding: 15px; border-radius: 12px; margin-bottom: 15px; border: 1px solid #30363D; }
    
    /* PLAY ALL BUTTON */
    .play-all-btn {
        background: #238636;
        color: white;
        width: 100%;
        padding: 18px;
        border: none;
        border-radius: 12px;
        cursor: pointer;
        font-size: 1.3em;
        font-weight: 800;
        text-align: center;
        text-decoration: none;
        display: block;
        box-shadow: 0 4px 15px rgba(35, 134, 54, 0.4);
        transition: transform 0.2s;
    }
    .play-all-btn:hover { transform: scale(1.02); background: #2ea043; }

</style>
""", unsafe_allow_html=True)

# --- SIDEBAR (Original Content) ---
with st.sidebar:
    st.markdown("### System Capabilities")
    
    st.markdown("""
    <div class='utility-box'>
    <b>1. The Truth Filter (API)</b><br>
    <small>Chatbots hallucinate songs. We ping the YouTube Music API to verify every track exists and is playable before showing it to you.</small>
    </div>
    
    <div class='utility-box'>
    <b>2. Zero-Friction Queue</b><br>
    <small>Don't copy-paste 10 times. We aggregate Video IDs into a single "Play All" link. 10 minutes of manual work becomes 1 click.</small>
    </div>

    <div class='utility-box'>
    <b>3. Visual Data Sorting</b><br>
    <small>Text is slow. Use Album Art to instantly distinguish between a "1930s Original" (grainy cover) and a "2024 Cover" (digital art).</small>
    </div>
    """, unsafe_allow_html=True)

# --- MAIN APP ---
st.markdown("<h1>VibeCheck</h1>", unsafe_allow_html=True)
st.write("Generate intelligent, cross-era soundtracks with API validation and auto-queuing.")

# --- PRO HINTS MODULE (Original Content) ---
with st.expander("💡 PRO TIP: How to describe complex scenes"):
    st.markdown("""
    * **Length is good:** Feel free to paste a full paragraph. The AI loves detail about lighting, weather, and character emotion.
    * **Contrast helps:** phrases like *"A violent fight scene with peaceful classical music"* give very specific results.
    * **Specifics matter:** *"Flickering neon lights in rain"* pulls different songs than just *"Cyberpunk City."*
    """)

# --- INPUT SECTION ---
with st.form(key='my_form', clear_on_submit=False):
    col_in, col_opt = st.columns([3, 1])
    with col_in:
        user_input = st.text_input(
            "Book Title or Scene Description:", 
            placeholder="e.g. 'The Age of Reason' by Sartre —OR— 'A tense dinner party that turns into a fist fight'"
        )

    with col_opt:
        reading_mode = st.toggle("📖 Reading Mode", value=False, help="Forces Instrumental/Ambient music only (No Lyrics).")
        num_songs = st.slider("Tracks", 3, 40, 12)
        
    submit_button = st.form_submit_button(label="ACTION: CURATE MIX")

# --- APP LOGIC ---
if submit_button:
    if not user_input:
        st.warning("Please provide a scene or book title.")
    else:
        client = Groq(api_key=GROQ_API_KEY)
        yt = YTMusic()
        
        music_type = "INSTRUMENTAL / AMBIENT / SCORE ONLY (NO LYRICS)" if reading_mode else "ANY (Lyrics allowed if thematic)"
        lessons = "\n".join([f"- {l}" for l in st.session_state.memory])
        
        with st.spinner("Synthesizing eras & validating IDs..."):
            try:
                # --- PROMPT LOGIC ---
                prompt = f"""
                Act as a Cinema Music Supervisor.
                INPUT: "{user_input}"
                MODE: {music_type}
                COUNT: {num_songs} tracks.
                HISTORY: {lessons}

                THE RULES OF THE MIX:
                1. MASTER TONE (CRITICAL): Identify the "World Physics" (e.g., Sally Rooney = Quiet/Intimate). Do NOT break this tone.
                2. QUALITY CONTROL: Prioritize "Hidden Gems" (Underground but Professional) or "Established Classics". Avoid low-quality trash.
                3. THE "SMART PLATTER": Mix eras (Old vs New) but keep them emotionally consistent.
                
                Output JSON:
                {{
                  "vision": "Explain the Master Tone and why these tracks fit.",
                  "search_queries": ["Artist - Song Title"],
                  "lesson": "One takeaway about this specific vibe."
                }}
                """
                
                completion = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[{"role": "user", "content": prompt}],
                    response_format={"type": "json_object"}
                )
                data = json.loads(completion.choices[0].message.content)
                
                if "lesson" in data:
                    st.session_state.memory.append(data["lesson"])

                st.markdown(f"### 👁️ Director's Vision")
                st.markdown(f"<div class='vision-box'>{data.get('vision')}</div>", unsafe_allow_html=True)
                st.divider()
                
                video_ids = []
                cols = st.columns(4) 
                
                for idx, q in enumerate(data.get('search_queries', [])):
                    # --- SEARCH LOGIC ---
                    res = yt.search(q)
                    match = None
                    
                    if res:
                         # --- THE VIP FILTER SYSTEM ---
                        for r in res[:5]:
                            # Skip short tracks (< 60s)
                            duration = r.get('duration_seconds', 0)
                            if not duration and 'duration' in r: pass 
                            if duration and duration < 60: continue
                            
                            # RULE 1: OFFICIAL SONGS (The VIPs)
                            if r['resultType'] == 'song':
                                match = r
                                break
                                
                            # RULE 2: USER VIDEOS (Must have K/M views)
                            if r['resultType'] == 'video':
                                views = r.get('views', '')
                                if 'K' in views or 'M' in views or 'B' in views:
                                    match = r
                                    break
                        
                        if match:
                            title = match['title']
                            artist = match['artists'][0]['name'] if match.get('artists') else "Unknown"
                            thumb = match['thumbnails'][-1]['url'] if match.get('thumbnails') else "https://via.placeholder.com/300"
                            video_ids.append(match['videoId'])
                            
                            # --- UI UPGRADE: CUSTOM HTML CARD ---
                            # Instead of st.image/st.write, we render a pure HTML card.
                            # This ensures perfect alignment and makes the whole card clickable.
                            with cols[idx % 4]:
                                st.markdown(f"""
                                <a href="https://music.youtube.com/watch?v={match['videoId']}" target="_blank" class="card-link">
                                    <div class="music-card">
                                        <img src="{thumb}" class="card-img">
                                        <div class="card-title" title="{title}">{title}</div>
                                        <div class="card-artist">{artist}</div>
                                    </div>
                                </a>
                                """, unsafe_allow_html=True)

                if video_ids:
                    url = f"http://www.youtube.com/watch_videos?video_ids={','.join(video_ids)}"
                    st.markdown("<br>", unsafe_allow_html=True)
                    st.markdown(f'<a href="{url}" target="_blank" class="play-all-btn">🚀 PLAY FULL SMART MIX ({len(video_ids)} Tracks)</a>', unsafe_allow_html=True)

            except Exception as e:
                st.error(f"Error: {e}")
