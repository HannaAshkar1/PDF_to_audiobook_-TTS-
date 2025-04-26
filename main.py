import os
import pdfplumber
import openai
from pathlib import Path
from pydub import AudioSegment

openai.api_key = os.getenv("OPENAI_API_KEY")


def chunk_text(text, max_chars=4000):
    words = text.split()
    chunks, current = [], []
    length = 0
    for w in words:
        # If adding this word would exceed our max, start a new chunk
        if length + len(w) + 1 > max_chars:
            chunks.append(" ".join(current))
            current, length = [], 0
        current.append(w)
        length += len(w) + 1  # +1 for the space
    if current:
        chunks.append(" ".join(current))
    return chunks


def extract_text_from_pdf(pdf_path):
    full_text = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                full_text.append(text)
    return "\n\n".join(full_text)


def synthesize_chunks(chunks, voice="alloy", model="tts-1-hd", output_dir="audio_chunks"):
    os.makedirs(output_dir, exist_ok=True)
    files = []
    for i, chunk in enumerate(chunks, 1):
        mp3_path = Path(output_dir) / f"chunk_{i:03d}.mp3"
        response = openai.audio.speech.create(
            model=model,  # e.g. "tts-1" or "tts-1-hd"
            voice=voice,  # pick one of the available voices
            input=chunk  # the text to speak
        )
        # This streams the MP3 binary directly into our file
        response.stream_to_file(str(mp3_path))
        print(f"Saved {mp3_path}")
        files.append(str(mp3_path))
    return files


def concatenate_audio(files, output_file="audiobook.mp3"):
    """
    Load each MP3 in order and append it to one big AudioSegment.
    Then export the combined segment as a single MP3.
    """
    combined = AudioSegment.empty()
    for f in files:
        combined += AudioSegment.from_mp3(f)
    combined.export(output_file, format="mp3")
    print(f"Created final audiobook: {output_file}")


def pdf_to_audiobook(pdf_path):
    print("Extracting PDF text…")
    text = extract_text_from_pdf(pdf_path)

    print("Splitting into chunks…")
    chunks = chunk_text(text)
    print(f"{len(chunks)} chunks to process.")

    files = synthesize_chunks(chunks)
    concatenate_audio(files)


if __name__ == "__main__":
    import sys

    if len(sys.argv) != 2:
        print("Usage: python audiobook.py path/to/book.pdf")
    else:
        pdf_to_audiobook(sys.argv[1])
