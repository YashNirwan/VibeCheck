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
    st.warning("⚠️ Using insecure fallback key.")
    GROQ_API_KEY = "gsk_..." 

if 'memory' not in st.session_state:
    st.session_state.memory = []

# --- UI STYLING ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;800&display=swap');
    .stApp { background-color: #0E1117; color: white; }
    h1 {
        font-family: 'Inter', sans-serif;
        font-weight: 800;
        font-size: 3.5rem !important;
        background: -webkit-linear-gradient(#eee, #999);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        padding-bottom: 20px;
    }
    .stTextInput > div > div > input { background-color: #1E1E2E; color: #00FFAA; border-radius: 8px; border: 1px solid #333; }
    div[data-testid="stFormSubmitButton"] > button {
        background: linear-gradient(90deg, #6a11cb 0%, #2575fc 100%);
        color: white; border: none; padding: 15px; font-weight: bold; border-radius: 8px; width: 100%;
        font-size: 1.1em; letter-spacing: 1px;
    }
    .vision-box { border-left: 4px solid #2575fc; padding: 20px; background: #161B22; border-radius: 0 10px 10px 0; }
    .utility-box { background: #1E1E2E; padding: 15px; border-radius: 8px; margin-bottom: 10px; border: 1px solid #333; }
</style>
""", unsafe_allow_html=True)

# --- SIDEBAR (RESTORED CONTENT) ---
with st.sidebar:
    st.markdown("### System Capabilities")
    st.markdown("""
    <div class='utility-box'>
    <b>1. The Truth Filter</b><br>
    <small>Verifying tracks against the database to ensure zero hallucinations.</small>
    </div>
    <div class='utility-box'>
    <b>2. The "VIP Entrance"</b><br>
    <small>Official Songs (YT Music exclusives) get VIP entry. User videos must prove popularity (1K+ views) to enter.</small>
    </div>
    <div class='utility-box'>
    <b>3. Master Tone Guard</b><br>
    <small>Ensuring a consistent emotional world across all tracks.</small>
    </div>
    """, unsafe_allow_html=True)

# --- MAIN APP ---
st.markdown("<h1>VibeCheck</h1>", unsafe_allow_html=True)

# --- PRO HINTS (RESTORED CONTENT) ---
with st.expander("💡 PRO TIP: How to describe complex scenes"):
    st.markdown("""
    * **Length is good:** Paste full paragraphs for better atmospheric matching.
    * **Contrast helps:** Try mixing opposing vibes like "Sad Classical" with "Aggressive Industrial."
    * **Visuals matter:** Mentioning colors or lighting helps the AI pick the right "texture."
    """)

# --- INPUT SECTION ---
with st.form(key='my_form', clear_on_submit=False):
    col_in, col_opt = st.columns([3, 1])
    with col_in:
        user_input = st.text_input("Book Title or Scene Description:", placeholder="e.g. 'The Age of Reason' by Sartre")
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
        music_type = "INSTRUMENTAL / AMBIENT / SCORE ONLY" if reading_mode else "ANY"
        lessons = "\n".join([f"- {l}" for l in st.session_state.memory])
        
        with st.spinner("Synthesizing eras & validating quality..."):
            try:
                prompt = f"""
                Act as a Cinema Music Supervisor.
                INPUT: "{user_input}"
                MODE: {music_type}
                COUNT: {num_songs} tracks.
                HISTORY: {lessons}

                CURATION PHILOSOPHY:
                - Mix "Hidden Gems" (underground but professional) with established classics.
                - DO NOT violate the Master Tone (the overarching mood of the author/scene).

                Output JSON:
                {{
                  "vision": "Define the Master Tone and why these tracks fit this specific world.",
                  "search_queries": ["Artist - Song Title"],
                  "lesson": "One insight about this vibe."
                }}
                """
                
                completion = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[{"role": "user", "content": prompt}],
                    response_format={"type": "json_object"}
                )
                data = json.loads(completion.choices[0].message.content)
                if "lesson" in data: st.session_state.memory.append(data["lesson"])

                st.markdown(f"### 👁️ Director's Vision")
                st.markdown(f"<div class='vision-box'>{data.get('vision')}</div>", unsafe_allow_html=True)
                st.divider()
                
                video_ids = []
                cols = st.columns(4) 
                
                for idx, q in enumerate(data.get('search_queries', [])):
                    res = yt.search(q)
                    match = None
                    
                    if res:
                        # --- THE VIP FILTER SYSTEM ---
                        # We scan the top 5 results to find the best version.
                        
                        for r in res[:5]:
                            # DURATION CHECK (Universal Rule):
                            # Skip if track is < 60 seconds (filters out skits/intros/ringtone uploads)
                            duration = r.get('duration_seconds', 0)
                            if not duration and 'duration' in r: 
                                pass # fallback for string parsing if needed
                            
                            if duration and duration < 60:
                                continue # Skip short tracks
                            
                            # RULE 1: OFFICIAL SONGS (The VIPs)
                            if r['resultType'] == 'song':
                                match = r
                                break
                                
                            # RULE 2: USER VIDEOS (The Crowd)
                            if r['resultType'] == 'video':
                                views = r.get('views', '')
                                # Must have K, M, or B views
                                if 'K' in views or 'M' in views or 'B' in views:
                                    match = r
                                    break
                        
                        # Final Check: Did we find a valid track?
                        if match:
                            title = match['title']
                            artist = match['artists'][0]['name'] if match.get('artists') else "Unknown"
                            thumb = match['thumbnails'][-1]['url'] if match.get('thumbnails') else ""
                            video_ids.append(match['videoId'])
                            
                            with cols[idx % 4]:
                                if thumb: st.image(thumb, use_container_width=True)
                                st.markdown(f"**{title}**")
                                st.caption(artist)
                                st.markdown(f"[▶ Listen](https://music.youtube.com/watch?v={match['videoId']})")
                                st.write("---")

                if video_ids:
                    url = f"http://www.youtube.com/watch_videos?video_ids={','.join(video_ids)}"
                    st.markdown(f'<a href="{url}" target="_blank"><button style="background:#2575fc;color:white;width:100%;padding:15px;border:none;border-radius:10px;cursor:pointer;font-size:1.2em;">🚀 PLAY FULL SMART MIX</button></a>', unsafe_allow_html=True)

            except Exception as e:
                st.error(f"Error: {e}")
