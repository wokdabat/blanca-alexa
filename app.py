import streamlit as st
import os
import tempfile
from io import BytesIO
import re

from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langchain_xai import ChatXAI
from langchain_core.messages import HumanMessage
from langchain_core.tools import tool

import requests
import yt_dlp
from faster_whisper import WhisperModel
from gtts import gTTS
from streamlit_mic_recorder import mic_recorder
from streamlit_player import st_player

# ========================== CONFIG ==========================
st.set_page_config(page_title="Blanca", page_icon="🐱", layout="wide")
st.title("🐱 Blanca")
st.caption("Your personal voice assistant powered by Grok")

XAI_API_KEY = os.getenv("XAI_API_KEY")
if not XAI_API_KEY:
    st.error("❌ Please set your XAI_API_KEY as an environment variable")
    st.stop()

llm = ChatXAI(model="grok-4-1-fast-reasoning", api_key=XAI_API_KEY, temperature=0.7)

# ========================== TOOLS ==========================
@tool
def youtube_search(query: str) -> str:
    """Search YouTube and return top results with playable links"""
    ydl_opts = {
        'quiet': True,
        'extract_flat': True,
        'no_warnings': True,
        'skip_download': True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        results = ydl.extract_info(f"ytsearch5:{query}", download=False)['entries']
    
    output = []
    for v in results:
        if v and v.get('id'):
            title = v.get('title', 'No title')
            url = f"https://youtube.com/watch?v={v['id']}"
            output.append(f"🎥 **{title}**\n🔗 {url}")
    
    return "\n\n".join(output) if output else "No results found on YouTube."

@tool
def get_weather(city: str) -> str:
    """Get current weather for a city in Fahrenheit"""
    city_coords = {
        "prosper": (33.24, -96.80), 
        "dallas": (32.78, -96.81),
        "new york": (40.71, -74.01), 
        "london": (51.51, -0.13),
        "paris": (48.86, 2.35)
    }
    lat, lon = city_coords.get(city.lower(), (32.78, -96.81))  # default near Dallas/Prosper
    
    # Added temperature_unit=fahrenheit
    url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true&temperature_unit=fahrenheit"
    
    try:
        data = requests.get(url).json()
        temp_f = data['current_weather']['temperature']
        windspeed = data['current_weather']['windspeed']
        return f"🌡️ **{city.title()}**: **{temp_f:.1f}°F**, Wind: {windspeed:.1f} km/h"
    except Exception:
        return f"Could not fetch weather for {city.title()}. Please try again."

@tool
def currency_exchange(from_currency: str, to_currency: str, amount: float = 1.0) -> str:
    """Convert currency"""
    url = f"https://api.frankfurter.app/latest?from={from_currency.upper()}&to={to_currency.upper()}"
    try:
        data = requests.get(url).json()
        rate = data.get("rates", {}).get(to_currency.upper())
        if rate:
            return f"💱 {amount} {from_currency.upper()} = **{amount * rate:.2f}** {to_currency.upper()}"
    except:
        pass
    return "Currency pair not supported right now."

tools = [youtube_search, get_weather, currency_exchange]
llm_with_tools = llm.bind_tools(tools)

# ========================== LANGGRAPH AGENT ==========================
class AgentState(dict):
    messages: list

def call_model(state: AgentState):
    return {"messages": [llm_with_tools.invoke(state["messages"])]}

def should_continue(state: AgentState):
    return "tools" if state["messages"][-1].tool_calls else END

graph = StateGraph(AgentState)
graph.add_node("agent", call_model)
graph.add_node("tools", ToolNode(tools))
graph.set_entry_point("agent")
graph.add_conditional_edges("agent", should_continue, {"tools": "tools", END: END})
graph.add_edge("tools", "agent")
agent = graph.compile()

# ========================== SESSION STATE ==========================
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "last_processed" not in st.session_state:
    st.session_state.last_processed = None

# ========================== VOICE & TEXT INPUT ==========================
st.subheader("🐈 Speak or type to Blanca")

col1, col2 = st.columns([1, 4])
with col1:
    audio = mic_recorder(
        start_prompt="🎙️ Record",
        stop_prompt="⏹️ Stop",
        just_once=True,
        key="voice_input"
    )

# Process voice input
if audio is not None:
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as f:
            f.write(audio["bytes"])
            temp_path = f.name

        model = WhisperModel("base", device="cpu", compute_type="int8")
        segments, _ = model.transcribe(
            temp_path, 
            beam_size=3, 
            language="en", 
            vad_filter=True
        )
        user_text = " ".join(s.text for s in segments).strip()
        os.unlink(temp_path)

        if user_text and len(user_text) > 5:
            st.success(f"✅ Blanca heard: **{user_text}**")
            st.session_state.chat_history.append(HumanMessage(content=user_text))
            st.rerun()
        else:
            st.warning("🤔 Blanca couldn't hear clearly. Please try speaking again.")
    except Exception as e:
        st.error(f"Voice processing error: {e}")

# Text input
user_input = st.chat_input("Type your message to Blanca...")
if user_input:
    st.session_state.chat_history.append(HumanMessage(content=user_input))

# ========================== RUN AGENT ==========================
if st.session_state.chat_history and isinstance(st.session_state.chat_history[-1], HumanMessage):
    last = st.session_state.chat_history[-1]
    if st.session_state.last_processed != last.content:
        with st.spinner("🤖 Blanca is thinking..."):
            result = agent.invoke({"messages": st.session_state.chat_history})
            ai_msg = result["messages"][-1]
            st.session_state.chat_history.append(ai_msg)
            st.session_state.last_processed = last.content

            # Text-to-Speech (skip for music responses)
            if ai_msg.content and "youtube.com" not in ai_msg.content.lower():
                try:
                    tts = gTTS(ai_msg.content[:450], lang="en")
                    fp = BytesIO()
                    tts.write_to_fp(fp)
                    fp.seek(0)
                    st.audio(fp, format="audio/mp3")
                except:
                    pass

# ========================== DISPLAY CHAT & PLAYERS ==========================
st.divider()

for msg in st.session_state.chat_history:
    if isinstance(msg, HumanMessage):
        st.chat_message("user").write(msg.content)
    else:
        st.chat_message("assistant").markdown(msg.content)
        
        # Auto-embed YouTube players when links appear
        if "youtube.com" in msg.content or "youtu.be" in msg.content:
            urls = re.findall(r'(https?://[^\s]+)', msg.content)
            for url in urls:
                if "youtube.com" in url or "youtu.be" in url:
                    st_player(url, height=300)
                    st.caption("▶️ Click the link above to open in full YouTube website")

# Instructions
st.caption("💡 Try saying: 'Blanca, play relaxing music with beach sounds' or 'What's the weather in Prosper?'")