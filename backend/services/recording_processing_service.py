import os

from services.audio_extraction_service import extract_audio_from_video
from services.speech_to_text_service import transcribe_audio


def process_recording(recording_path, file_type):
    """
    Process an uploaded interview recording.

    Video:
        Video → Audio → Transcript

    Audio:
        Audio → Transcript

    Returns:
        {
            "transcript": str,
            "audio_path": str | None
        }
    """

    if not os.path.exists(recording_path):
        raise FileNotFoundError(
            "Recording file not found"
        )

    audio_path = None

    try:

        # ---------------------------------------------
        # Video recording
        # ---------------------------------------------

        if file_type == "video":

            audio_path = extract_audio_from_video(
                recording_path
            )

            transcript = transcribe_audio(
                audio_path
            )

        # ---------------------------------------------
        # Audio recording
        # ---------------------------------------------

        elif file_type == "audio":

            audio_path = recording_path

            transcript = transcribe_audio(
                audio_path
            )

        else:

            raise ValueError(
                "Unsupported recording type"
            )

        return {
            "transcript": transcript,
            "audio_path": audio_path
        }

    finally:

        # ---------------------------------------------
        # Remove temporary extracted WAV file
        # ---------------------------------------------

        if (
            audio_path
            and audio_path != recording_path
            and os.path.exists(audio_path)
        ):
            os.remove(audio_path)