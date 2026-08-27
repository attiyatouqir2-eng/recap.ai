import yt_dlp
from pydub import AudioSegment
import os

DOWNLOAD_DIR = "downloads/"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

def download_audio_from_youtube(url :str) -> str:
    # FIRST: Get cookies from environment variable (MUST BE FIRST)
    cookies_content = os.getenv("YOUTUBE_COOKIES", "")
    
    # NOW you can use cookies_content in print statements
    print(f"Downloading: {url}")
    print(f"Cookies present: {bool(cookies_content)}")
    print(f"Cookie length: {len(cookies_content)} characters")
    
    # CLEAN OLD FILES: Remove all .wav files from downloads folder
    for file in os.listdir(DOWNLOAD_DIR):
        if file.endswith('.wav'):
            try:
                os.remove(os.path.join(DOWNLOAD_DIR, file))
            except:
                pass
    
    # Create temporary cookies file if cookies exist
    cookies_path = None
    if cookies_content:
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            f.write(cookies_content)
            cookies_path = f.name
    
    output_path = os.path.join(DOWNLOAD_DIR, "%(title)s.%(ext)s")
    ydl_opts = {
        "format": 'bestaudio/best',
        'outtmpl': output_path,
        "postprocessors": [
            {
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'wav',
                'preferredquality': '192',
            }
        ],
        "quiet": False,  # CHANGE TO False TO SEE ERRORS
        "socket_timeout": 30,
        "retries": 10,
        "fragment_retries": 10,
        "user_agent": 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        # "ignoreerrors": True,  # REMOVE THIS LINE
    }
    
    # Add cookies to options if available
    if cookies_path:
        ydl_opts["cookiefile"] = cookies_path
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            
            # Check if download was successful
            if info is None:
                raise Exception("Failed to download video")
            
            # Get the base filename
            base_filename = ydl.prepare_filename(info)
            base_name = os.path.splitext(base_filename)[0]
            base_name = os.path.basename(base_name)
            
            # Search for the WAV file
            wav_file = None
            for file in os.listdir(DOWNLOAD_DIR):
                if file.startswith(base_name) and file.endswith('.wav'):
                    wav_file = os.path.join(DOWNLOAD_DIR, file)
                    break
            
            if wav_file is None:
                # Try just finding any WAV file
                wav_files = [f for f in os.listdir(DOWNLOAD_DIR) if f.endswith('.wav')]
                if wav_files:
                    wav_file = os.path.join(DOWNLOAD_DIR, wav_files[-1])
                else:
                    # If no WAV, check if any file was downloaded
                    all_files = os.listdir(DOWNLOAD_DIR)
                    if all_files:
                        raise Exception(f"Files downloaded but no WAV found. Files: {all_files}")
                    else:
                        raise Exception("No file was downloaded. The video might be unavailable or blocked.")
            
            return wav_file
            
    except Exception as e:
        # Clean up and re-raise the error with more context
        raise Exception(f"YouTube download failed: {str(e)}")
        
    finally:
        # Clean up temporary cookie file
        if cookies_path and os.path.exists(cookies_path):
            os.remove(cookies_path)

def convert_to_wav(input_path: str) -> str:
  output_path = os.path.splitext(input_path)[0] + "_converted.wav"
  audio = AudioSegment.from_file(input_path)
  audio = audio.set_channels(1).set_frame_rate(16000)  # Convert to mono and set frame rate 16khz 
  audio.export(output_path, format="wav")
  return output_path



def chunk_audio(wav_path: str, chunk_minutes: int = 10 ) -> list:
   # Check if file exists
  if not os.path.exists(wav_path):
      raise FileNotFoundError(f"Audio file not found: {wav_path}")
  audio = AudioSegment.from_wav(wav_path)
  chunk_ms = chunk_minutes * 60 * 1000  # Convert minutes to milliseconds
  chunks = []
  for i, start in enumerate(range(0, len(audio), chunk_ms)):
    chunk = audio[start:start + chunk_ms]
    chunk_path  = f"{wav_path}_chunk_{i}.wav"
    chunk.export(chunk_path, format="wav")
    chunks.append(chunk_path)
  return chunks

def process_input(source: str) -> list:
  if source.startswith("http")or source.startswith("https://"):
    print("Detected YouTube URL. Downloading audio...")
    wav_path = download_audio_from_youtube(source)
  else:
    print("Processing local audio file...")
    wav_path = convert_to_wav(source)

  print("Chunking audio...")
  chunks = chunk_audio(wav_path)
  print(f"Audio ready - {len(chunks)} chunk(s) created.")
  return chunks
  
