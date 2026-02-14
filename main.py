from flask import Flask, render_template
from flask_socketio import SocketIO, join_room, leave_room, emit
from faster_whisper import WhisperModel
from deep_translator import GoogleTranslator
import edge_tts
import asyncio
import io
import base64

app = Flask(__name__)
socketio = SocketIO(app)

whisper_model = WhisperModel("base", device="cpu")

######## utils
def speech_to_text(audio_path):
    segments, _ = whisper_model.transcribe(audio_path)
    return " ".join([s.text for s in segments])

def translate_text(text, target_lang="en"):
    return GoogleTranslator(source="auto", target=target_lang).translate(text)

async def tts_edge(text, voice="en-US-JennyNeural"):
    communicate = edge_tts.Communicate(text, voice)
    buffer = io.BytesIO()
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            buffer.write(chunk["data"])
    buffer.seek(0)
    return base64.b64encode(buffer.read()).decode("utf-8")

# POLOWERA

@app.route("/")
def index():
    return render_template("phoneCall.html")

@app.route('/call', methods=['POST'])
def call():
    return "Call initiated"

# SocketIO events

@socketio.on("join")
def on_join(data):
    room = data["room"]
    join_room(room)
    emit("status", {"msg": f"{data['username']} joined {room}"}, room=room)

@socketio.on("leave")
def on_leave(data):
    room = data["room"]
    leave_room(room)
    emit("status", {"msg": f"{data['username']} left {room}"}, room=room)

@socketio.on("audio_chunk")
def handle_audio(data):
    room = data["room"]
    username = data["username"]
    target_lang = data.get("target_lang", "en")

    # Decode audio and save temp file
    audio_bytes = base64.b64decode(data["chunk"])
    temp_path = f"static/{username}_temp.wav"
    with open(temp_path, "wb") as f:
        f.write(audio_bytes)

    # STT
    text = speech_to_text(temp_path)

    # Translation
    translated = translate_text(text, target_lang)

    # TTS
    audio_base64 = asyncio.run(tts_edge(translated))

    # Send back only to other users in the same room
    emit("translated_audio", {"text": translated, "audio": audio_base64, "from": username}, room=room, include_self=False)


if __name__ == "__main__":
    socketio.run(app)