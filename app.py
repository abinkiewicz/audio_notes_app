from io import BytesIO
import streamlit as st
from audiorecorder import audiorecorder  # type: ignore
from dotenv import dotenv_values
from openai import OpenAI
from hashlib import md5

env = dotenv_values(".env")

AUDIO_TRANSCRIBE_MODEL = "whisper-1"

@st.cache_resource #decorator for saving openai key just once at the beginning 
def get_openai_client():
    return OpenAI(api_key=env["OPENAI_API_KEY"])

def transcribe_audio(audio_bytes):
    openai_client = get_openai_client()
    audio_file = BytesIO(audio_bytes)
    audio_file.name = "audio.mp3"
    transcript = openai_client.audio.transcriptions.create(
        file=audio_file,
        model=AUDIO_TRANSCRIBE_MODEL,
        response_format="verbose_json",
    )

    return transcript.text

#
# MAIN
#
st.set_page_config(page_title="Transcript me", layout="centered")

#OpenAI API key protection
if not st.session_state.get("openai_api_key"):
    if "OPENAI_API_KEY" in env:
        st.session_state["openai_api_key"] = env["OPENAI_API_KEY"]

    else:
        st.info("Dodaj swój klucz API OpenAI aby móc korzystać z tej aplikacji")
        st.session_state["openai_api_key"] = st.text_input("Klucz API", type="password")
        if st.session_state["openai_api_key"]:
            st.rerun()

#Stop rendering until theres no openai key
if not st.session_state.get("openai_api_key"):
    st.stop()


# Session state initialization
if "note_audio_bytes_md5" not in st.session_state:
    st.session_state["note_audio_bytes_md5"] = None

if "note_audio_bytes" not in st.session_state:
    st.session_state["note_audio_bytes"] = None

if "note_audio_text" not in st.session_state:
    st.session_state["note_audio_text"] = ""

st.title(":studio_microphone: Transcript me")
#Receiving segment (from pydub) with audio
note_audio = audiorecorder(
    start_prompt="Start recording",
    stop_prompt="Stop recording",
)

if note_audio:
    audio = BytesIO()
    note_audio.export(audio, format="mp3")
    st.session_state["note_audio_bytes"] = audio.getvalue()

    #Clearing transcription field after next recording
    current_md5 = md5(st.session_state["note_audio_bytes"]).hexdigest()
    if st.session_state["note_audio_bytes_md5"] != current_md5:
        st.session_state["note_audio_text"] = ""
        st.session_state["note_audio_bytes_md5"] = current_md5

    st.audio(st.session_state["note_audio_bytes"], format="audio/mp3")

    if st.button("Press to transcript"):
        st.session_state["note_audio_text"] = transcribe_audio(st.session_state["note_audio_bytes"])

    if st.session_state["note_audio_text"]:
        st.text_area("Edit note", value=st.session_state["note_audio_text"])
