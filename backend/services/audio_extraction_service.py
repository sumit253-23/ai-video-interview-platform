import os
import subprocess


def extract_audio_from_video(video_path):
    if not os.path.exists(video_path):
        raise FileNotFoundError("Video recording not found")

    audio_path = os.path.splitext(video_path)[0] + ".wav"

    command = [
        "ffmpeg",
        "-y",
        "-i",
        video_path,
        "-vn",
        "-acodec",
        "pcm_s16le",
        "-ar",
        "16000",
        "-ac",
        "1",
        audio_path,
    ]

    try:
        subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True,
        )

        if not os.path.exists(audio_path):
            raise RuntimeError("FFmpeg did not create the audio file")

        return audio_path

    except subprocess.CalledProcessError as e:
        raise RuntimeError(
            f"FFmpeg audio extraction failed:\n{e.stderr}"
        )