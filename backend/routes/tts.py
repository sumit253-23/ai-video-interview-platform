from flask import Blueprint, request, send_file, jsonify
from services.tts_service import generate_speech
import os


tts_bp = Blueprint("tts", __name__, url_prefix="/api/tts")


@tts_bp.route("/speak", methods=["POST"])
def speak():
    try:
        data = request.get_json()

        if not data or not data.get("text"):
            return jsonify({
                "status": "error",
                "message": "Text is required"
            }), 400

        text = data["text"].strip()

        audio_path = generate_speech(text)

        if not os.path.exists(audio_path):
            return jsonify({
                "status": "error",
                "message": "Audio generation failed"
            }), 500

        return send_file(
            audio_path,
            mimetype="audio/mpeg",
            as_attachment=False
        )

    except Exception as e:
        print("TTS ERROR:", e)

        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500