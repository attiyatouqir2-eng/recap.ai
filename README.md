# 🎙️ Recap — AI Meeting Assistant

Recap turns raw meeting audio into structured, searchable insights. Give it a YouTube link or an audio file, and it will transcribe, translate, summarize, and let you chat with the meeting afterward.

## Features

- 🎧 Accepts audio from YouTube URLs or uploaded files
- 📝 Local transcription using OpenAI's Whisper (no cloud transcription costs)
- 🌐 Automatic Hindi → English translation
- 🤖 AI-powered summarization, action item extraction, and key decision detection (via LangChain + Mistral API)
- 💬 Chat with your meeting transcript using a RAG pipeline (ChromaDB + HuggingFace embeddings)
- 📄 Export results as TXT
- 🖥️ Clean Streamlit web interface

## Tech Stack

- **Frontend**: Streamlit
- **Transcription**: OpenAI Whisper (local)
- **LLM orchestration**: LangChain (LCEL)
- **LLM**: Mistral API
- **Vector store**: ChromaDB
- **Embeddings**: HuggingFace Sentence Transformers
- **Audio processing**: yt-dlp, pydub, ffmpeg

## Getting Started

### Prerequisites

- Python 3.11+
- ffmpeg installed and available on PATH
- A [Mistral API key](https://console.mistral.ai/)

### Installation

```bash
git clone https://github.com/YOUR_USERNAME/recap-ai-meeting-assistant.git
cd recap-ai-meeting-assistant
python -m venv .venv
.venv\Scripts\activate   # Windows
pip install -r requirements.txt
```

### Configuration

Create a `.env` file in the project root:
MISTRAL_API_KEY=your_api_key_here

### Running the app

```bash
streamlit run app.py
```

## Notes

- Whisper's `small`/`medium` models can be slow on CPU-only machines. The `tiny` model is recommended for lower-end hardware.
- ffmpeg must be installed separately and available on your system PATH.

## License

[Choose a license, e.g. MIT]
