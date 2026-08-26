import os
import tempfile
import time

import streamlit as st
from dotenv import load_dotenv

from utils.audio_processor import process_input
from core.transcriber import transcribe_all
from core.summarize import summarize, generate_title
from core.extractor import extract_action_items, extract_key_decisions, extract_questions
from core.rag_engine import build_rag_chain, ask_questions

load_dotenv()

# --------------------------------------------------------------------------
# Page config
# --------------------------------------------------------------------------
st.set_page_config(
    page_title="Recap.ai - AI Meeting Assistant",
    page_icon="🎙️",
    layout="wide",
)

# --------------------------------------------------------------------------
# Session state defaults
# --------------------------------------------------------------------------
if "result" not in st.session_state:
    st.session_state.result = None
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "processing" not in st.session_state:
    st.session_state.processing = False


# --------------------------------------------------------------------------
# Pipeline runner (mirrors your CLI run_pipeline, with progress feedback)
# --------------------------------------------------------------------------
def run_pipeline(source: str, language: str, whisper_model: str, translate: bool) -> dict:
    os.environ["WHISPER_MODEL"] = whisper_model

    status = st.status("Starting AI Meeting Assistant...", expanded=True)

    status.write("Preparing audio (downloading / converting / chunking)...")
    chunks = process_input(source)
    status.write(f"Audio ready — {len(chunks)} chunk(s) created.")

    status.write("Transcribing audio... this can take a while on CPU, please be patient.")
    t0 = time.time()
    transcript = transcribe_all(chunks, translate=translate)
    status.write(f"Transcription complete in {time.time() - t0:.0f}s.")

    status.write("Generating title and summary...")
    title = generate_title(transcript)
    summary = summarize(transcript)

    status.write("Extracting action items, decisions, and open questions...")
    action_items = extract_action_items(transcript)
    decisions = extract_key_decisions(transcript)
    questions = extract_questions(transcript)

    status.write("Building RAG chat index over the transcript...")
    rag_chain = build_rag_chain(transcript)

    status.update(label="Done!", state="complete", expanded=False)

    return {
        "transcript": transcript,
        "title": title,
        "summary": summary,
        "action_items": action_items,
        "decisions": decisions,
        "questions": questions,
        "rag_chain": rag_chain,
    }


# --------------------------------------------------------------------------
# Export helpers
# --------------------------------------------------------------------------
def build_txt_export(result: dict) -> str:
    parts = [
        f"TITLE: {result['title']}",
        "=" * 60,
        "SUMMARY",
        "=" * 60,
        result["summary"],
        "",
        "ACTION ITEMS",
        "=" * 60,
        str(result["action_items"]),
        "",
        "KEY DECISIONS",
        "=" * 60,
        str(result["decisions"]),
        "",
        "OPEN QUESTIONS",
        "=" * 60,
        str(result["questions"]),
        "",
        "FULL TRANSCRIPT",
        "=" * 60,
        result["transcript"],
    ]
    return "\n".join(parts)


# --------------------------------------------------------------------------
# Sidebar — input & settings
# --------------------------------------------------------------------------
with st.sidebar:
    st.title("🎙️ Recap.ai")
    st.caption("Transcribe, summarize, and chat with your meetings.")

    st.divider()

    input_mode = st.radio("Source", ["YouTube URL", "Upload audio file"])

    source = None
    if input_mode == "YouTube URL":
        source = st.text_input("YouTube URL", placeholder="https://www.youtube.com/watch?v=...")
    else:
        uploaded_file = st.file_uploader(
            "Upload audio file", type=["mp3", "wav", "m4a", "mp4", "webm", "ogg"]
        )
        if uploaded_file is not None:
            tmp_dir = tempfile.gettempdir()
            tmp_path = os.path.join(tmp_dir, uploaded_file.name)
            with open(tmp_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            source = tmp_path

    st.divider()

    language = st.selectbox("Spoken language", ["english", "hindi", "auto"], index=0)
    translate = language == "hindi"

    whisper_model = st.selectbox(
        "Whisper model",
        ["tiny", "base", "small", "medium"],
        index=0,
        help="Smaller = faster, less accurate. On CPU-only machines, 'tiny' or 'base' is strongly recommended.",
    )
    if whisper_model in ("small", "medium"):
        st.warning(
            "This model can be very slow on CPU-only machines with limited RAM. "
            "Consider 'tiny' or 'base' unless you have a GPU or 16GB+ RAM.",
            icon="⚠️",
        )

    st.divider()

    run_clicked = st.button("Run Analysis", type="primary", use_container_width=True, disabled=not source)

    if st.session_state.result is not None:
        if st.button("Start New Meeting", use_container_width=True):
            st.session_state.result = None
            st.session_state.chat_history = []
            st.rerun()


# --------------------------------------------------------------------------
# Run pipeline
# --------------------------------------------------------------------------
if run_clicked and source:
    try:
        st.session_state.result = run_pipeline(source, language, whisper_model, translate)
        st.session_state.chat_history = []
    except Exception as e:
        st.error(f"Something went wrong while processing: {e}")
        st.session_state.result = None


# --------------------------------------------------------------------------
# Main area
# --------------------------------------------------------------------------
result = st.session_state.result

if result is None:
    st.title("🎙️ Recap")
    st.info("👈 Add a YouTube URL or upload an audio file in the sidebar, then click **Run Analysis**.")
    st.markdown(
        """
        **What this does:**
        - Transcribes meeting audio locally with Whisper
        - Translates Hindi → English automatically if needed
        - Summarizes the meeting and pulls out action items, decisions, and open questions
        - Lets you chat with the transcript using a RAG pipeline
        - Exports everything as a TXT file
        """
    )
else:
    st.title(result["title"])

    tabs = st.tabs(["📝 Summary", "🟩 Action Items", "📌 Decisions", "❓ Questions", "📜 Transcript", "💬 Chat"])

    with tabs[0]:
        st.markdown(result["summary"])

    with tabs[1]:
        st.markdown(result["action_items"])

    with tabs[2]:
        st.markdown(result["decisions"])

    with tabs[3]:
        st.markdown(result["questions"])

    with tabs[4]:
        st.text_area("Full transcript", result["transcript"], height=400)

    with tabs[5]:
        st.caption("Ask questions about this meeting — answers are grounded in the transcript.")

        for role, msg in st.session_state.chat_history:
            with st.chat_message(role):
                st.markdown(msg)

        question = st.chat_input("Ask something about this meeting...")
        if question:
            st.session_state.chat_history.append(("user", question))
            with st.chat_message("user"):
                st.markdown(question)

            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):
                    answer = ask_questions(result["rag_chain"], question)
                st.markdown(answer)
            st.session_state.chat_history.append(("assistant", answer))

    st.divider()
    st.subheader("📤 Export")

    st.download_button(
        "⬇ Download as TXT",
        data=build_txt_export(result),
        file_name="meeting_report.txt",
        mime="text/plain",
        use_container_width=True,
    )
