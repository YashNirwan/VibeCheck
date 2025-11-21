import streamlit as st
from groq import Groq
from ytmusicapi import YTMusic
import json

# --- PAGE CONFIG ---
st.set_page_config(page_title="VibeCheck", page_icon="🎬", layout="wide")

# --- 🔐 SECURITY: GET KEY FROM CLOUD SECRETS ---
# We use st.secrets so we don't expose the key in the code
try:
    GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
except:
    st.error("🚨 API Key not found! Please set it in Streamlit Secrets.")
    st.stop()

# Initialize Memory
if 'memory' not in st.session_state:
    st.session_state.memory = []

# --- UI STYLING (Minimalist Font) ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;800&display=swap');
    
    .stApp { background-color: #0E1117; color: white; }
    
    h1 {
        font-family: 'Inter', sans-serif;
        font-weight: 800;
        letter-spacing: -1px;
        font-size: 3.5rem !important;
        background: -webkit-linear-gradient(#eee, #999);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        padding-bottom: 20px;
    }
    
    .stTextInput > div > div > input { background-color: #1E1E2E; color: #00FFAA; border-radius: 8px; border: 1px solid #333; }
    .stButton > button {
        background: linear-gradient(90deg, #6a11cb 0%, #2575fc 100%);
        color: white; border: none; padding: 15px; font-weight: bold; border-radius: 8px; width: 100%;
        font-size: 1.1em; letter-spacing: 1px;
    }
    .track-card { background: #161B22; padding: 10px; border-radius: 10px; margin-bottom: 10px; }
    .vision-box { border-left: 4px solid #2575fc; padding: 20px; background: #161B22; border-radius: 0 10px 10px 0; }
    .utility-box { background: #1E1E2E; padding: 15px; border-radius: 8px; margin-bottom: 10px; border: 1px solid #333; }
</style>
""", unsafe_allow_html=True)

# --- SIDEBAR: HARD UTILITY ---
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

# --- INPUT SECTION ---
col_in, col_opt = st.columns([3, 1])
with col_in:
    user_input = st.text_input(
        "Book Title or Scene Description:", 
        placeholder="e.g. 'The Age of Reason' by Sartre —OR— 'A tense dinner party that turns into a fist fight'"
    )

with col_opt:
    reading_mode = st.toggle("📖 Reading Mode", value=False, help="Forces Instrumental/Ambient music only (No Lyrics).")
    num_songs = st.slider("Tracks", 3, 40, 12)

# --- 💡 PRO HINTS MODULE ---
with st.expander("💡 PRO TIP: How to describe complex scenes"):
    st.markdown("""
    * **Length is good:** Feel free to paste a full paragraph. The AI loves detail about lighting, weather, and character emotion.
    * **Contrast helps:** phrases like *"A violent fight scene with peaceful classical music"* give very specific results.
    * **Specifics matter:** *"Flickering neon lights in rain"* pulls different songs than just *"Cyberpunk City."*
    """)

if st.button("ACTION: CURATE MIX"):
    if not user_input:
        st.warning("Please provide a scene or book title.")
    else:
        client = Groq(api_key=GROQ_API_KEY)
        yt = YTMusic()
        
        # Memory String
        lessons = "\n".join([f"- {l}" for l in st.session_state.memory])
        
        music_type = "INSTRUMENTAL / AMBIENT / SCORE ONLY (NO LYRICS)" if reading_mode else "ANY (Lyrics allowed if thematic)"
        
        with st.spinner("Synthesizing eras & validating IDs..."):
            try:
                prompt = f"""
                Act as a Cinema Music Supervisor known for "anachronistic but perfect" choices.
                INPUT: "{user_input}"
                MODE: {music_type}
                COUNT: {num_songs} tracks.
                HISTORY: {lessons}

                THE RULES OF THE MIX:
                1. PRIORITY = EMOTIONAL TRUTH. Does it *feel* right?
                2. THE "SMART PLATTER": You MUST provide a mix of eras. 
                   - If it's an old book (Sartre), do NOT just give 1930s music.
                   - Include 1-2 period accurate tracks (to ground it).
                   - Include modern tracks that share the *philosophy* (e.g., Radiohead or Max Richter for existentialism).
                   - Include "Bridge" tracks (Dark Ambient, Jazz Noir).
                3. READING MODE CHECK: If mode is Instrumental, ensure you still mix Classical with Modern Ambient/Drone.
                4. Return exactly {num_songs} tracks.

                Output JSON:
                {{
                  "vision": "Explain why you mixed these specific eras. What connects the 1930s track to the 2024 track?",
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
                    res = yt.search(q, filter="songs")
                    if res:
                        track = res[0]
                        title = track['title']
                        artist = track['artists'][0]['name']
                        thumb = track['thumbnails'][-1]['url'] if track['thumbnails'] else "https://via.placeholder.com/150"
                        video_ids.append(track['videoId'])
                        
                        with cols[idx % 4]:
                            st.image(thumb, use_container_width=True)
                            st.markdown(f"**{title}**")
                            st.caption(artist)
                            st.markdown(f"[▶ Listen](https://music.youtube.com/watch?v={track['videoId']})")
                            st.write("---")

                if video_ids:
                    url = f"http://www.youtube.com/watch_videos?video_ids={','.join(video_ids)}"
                    st.markdown(f'<a href="{url}" target="_blank"><button style="background:#2575fc;color:white;width:100%;padding:15px;border:none;border-radius:10px;cursor:pointer;font-size:1.2em;">🚀 PLAY FULL SMART MIX</button></a>', unsafe_allow_html=True)

            except Exception as e:
                st.error(f"Error: {e}")