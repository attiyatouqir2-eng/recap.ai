from dotenv import load_dotenv
from utils.audio_processor import process_input
from core.transcriber import transcribe_all
from core.summarize import summarize, generate_title
from core.extractor import extract_action_items, extract_key_decisions, extract_questions
from core.rag_engine import build_rag_chain, ask_questions

load_dotenv() 

def run_pipeline(source: str, language: str = "english") -> dict:
    print("Starting AI Video Assisstant")
    chunks = process_input(source)
    transcript = transcribe_all(chunks, language)
    print(f"raw transcription(first 300 characters): {transcript[:300]}")

    title = generate_title(transcript)
    summary = summarize(transcript)


    action_items = extract_action_items(transcript)
    decisions = extract_key_decisions(transcript)
    questions = extract_questions(transcript)

    rag_chain = build_rag_chain(transcript)

    return {
        "transcript": transcript,
        "title": title,
        "summary": summary,
        "action_items": action_items,
        "decisions": decisions,
        "questions": questions,
        "rag_chain": rag_chain
    }

if __name__ == "__main__":
    source = input("Enter YouTube URL or local audio file path: ").strip()
    language = "english"  
    result = run_pipeline(source, language)

    print("\n" + "=" * 60)
    print(f"TITLE: {result['title']}")
    print("=" * 60)
    print("\nSUMMARY")
    print("=" * 60)
    print(result['summary'])

    print("\n" + "=" * 60)
    print("🟩 ACTION ITEMS")
    print("=" * 60)
    print(result['action_items'])

    print("\n" + "=" * 60)
    print("📌 KEY DECISIONS")
    print("=" * 60)
    print(result['decisions'])

    print("\n" + "=" * 60)
    print("❓ OPEN QUESTIONS")
    print("=" * 60)
    print(result['questions'])

    # Phase 2 - Chat with your meeting via RAG
print("\nChat with your meeting (type 'exit' to quit)\n")
rag_chain = result["rag_chain"]
while True:
    question = input("You: ").strip()
    if question.lower() in ["exit", "quit", "q"]:
        print("Goodbye!")
        break
    if not question:
        continue
    answer = ask_questions(rag_chain, question)
    print(f"\n Assistant: {answer}\n")
