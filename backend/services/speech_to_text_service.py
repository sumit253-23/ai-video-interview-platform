import os

from groq import Groq


client = Groq(
    api_key=os.getenv("GROQ_API_KEY")
)


def transcribe_audio(file_path):
    """
    Convert an audio/video recording into text.

    The recording file must already exist on disk.
    """

    if not os.path.exists(file_path):
        raise FileNotFoundError(
            "Recording file not found"
        )

    with open(file_path, "rb") as audio_file:

        transcription = client.audio.transcriptions.create(
            file=audio_file,
            model="whisper-large-v3-turbo",
            response_format="text"
        )

    return transcription.strip()