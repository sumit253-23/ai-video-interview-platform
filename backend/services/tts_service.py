from gtts import gTTS
import os
import uuid


def generate_speech(text):
    if not text or not text.strip():
        raise ValueError("Text is required for speech generation")

    output_dir = os.path.join("uploads", "tts")

    os.makedirs(output_dir, exist_ok=True)

    filename = f"tts_{uuid.uuid4().hex}.mp3"
    output_path = os.path.join(output_dir, filename)

    tts = gTTS(
        text=text.strip(),
        lang="en",
        slow=False
    )

    tts.save(output_path)

    return output_path