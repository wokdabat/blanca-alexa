# 🐱 Blanca - Your Personal Voice Assistant

A custom voice/text assistant powered by **Grok (xAI)**, built with **Streamlit**, **LangGraph**, and **Whisper**.

Blanca can:
- Answer general questions
- Search YouTube and play music (with embedded player)
- Get current weather (in °F)
- Convert currencies
- Understand voice input (click the cat icon 🐈 to speak)

## Features
- Voice input with local Whisper transcription (fast & private)
- Text input fallback
- Embedded YouTube player for music requests
- Newest messages appear at the top
- Personalized responses as "Blanca"

## How to Run Locally

### Prerequisites
- Python 3.10+
- [uv](https://docs.astral.sh/uv/) (recommended) or pip

### Setup

```bash
# 1. Clone the repository
git clone https://github.com/wokdabat/blanca-alexa.git
cd blanca-alexa

# 2. Create and activate virtual environment
uv venv
.venv\Scripts\activate    # Windows
# source .venv/bin/activate   # macOS/Linux

# 3. Install dependencies
uv pip install -r requirements.txt

# 4. Set up your xAI API key
mkdir -p .streamlit
echo 'XAI_API_KEY = "xai-your_actual_key_here"' > .streamlit/secrets.toml

# 5. Run the app
uv run streamlit run .\app.py

# 6. Try These Commands
"What's the weather in Prosper?"
"Blanca, play relaxing music with beach sounds"
"Convert 100 USD to EUR"
"Blanca, search YouTube for lo-fi beats"

# 7. Tech Stack
LLM: Grok (grok-4-1-fast-reasoning) via xAI API
Framework: Streamlit + LangGraph (ReAct agent)
Voice: st.audio_input + faster-whisper
YouTube: yt-dlp + streamlit-player
Tools: Weather (Open-Meteo), Currency (Frankfurter)

# 8. Project Structure
blanca-alexa/
├── app.py
├── requirements.txt
├── .gitignore
├── .streamlit/
│   └── secrets.toml          # ← Not committed
├── README.md
└── pyproject.toml (optional)

Made with ❤️ using Grok.