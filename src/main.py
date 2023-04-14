"""
This module implements a voice-controlled chatbot called Nova, which utilizes Google's Speech Recognition API
for speech-to-text and GPT-3 for generating responses. The chatbot can be activated by saying "Hello Nova"
and will continue to listen and respond until the user says "Bye Nova".
"""
import json
import io
from typing import Optional
import argparse

import simpleaudio as sa
import speech_recognition as sr
from pydub import AudioSegment
from gtts import gTTS
from tempfile import NamedTemporaryFile

from revChatGPT.V1 import Chatbot


def listen() -> sr.AudioData:
    """
    Record audio from the user's microphone and return the audio data.
    """
    r = sr.Recognizer()
    with sr.Microphone(sample_rate=16000, chunk_size=1024) as source:
        r.adjust_for_ambient_noise(source)
        audio = r.listen(source, phrase_time_limit=10)
    return audio


def transcribe(audio_data: sr.AudioData, lang: str = 'en') -> str:
    """
    Transcribe audio data using Google Speech Recognition and return the text transcription.
    """
    # create a language_dict to map lang keys to corresponding language codes
    language_dict = {
        'en': 'en-US',
        'es': 'es-ES'
    }

    r = sr.Recognizer()

    try:
        text = r.recognize_google(
            audio_data, language=language_dict.get(lang, 'en-US'))
        print("Transcription: ", text)
        return text
    except sr.UnknownValueError:
        print("Google Speech Recognition could not understand audio")
        return ""
    except sr.RequestError as e:
        print(
            f"Could not request results from Google Speech Recognition service; {e}")
        return ""


def synthesize(text: str, lang: str = 'en', speed_multiplier: Optional[float] = 1.25) -> None:
    """
    Synthesize the given text using gTTS and play the resulting audio with simpleaudio.
    """
    # create a tld_dict to map lang keys to corresponding tld values
    tld_dict = {
        'en': 'com.au',
        'es': 'es'
    }

    if len(text.strip()) > 0:
        tts = gTTS(text=text, lang=lang,
                   tld=tld_dict.get(lang, 'com.au'))
        with NamedTemporaryFile(delete=True) as f:
            tts.save(f.name)

            audio = AudioSegment.from_file(f.name)
            audio_with_changed_speed = audio.speedup(
                playback_speed=speed_multiplier)

            # Save the file to a BytesIO object
            buffer = io.BytesIO()
            audio_with_changed_speed.export(buffer, format="wav")

            # Play the audio using simpleaudio
            buffer.seek(0)
            wave_obj = sa.WaveObject.from_wave_file(buffer)
            play_obj = wave_obj.play()
            play_obj.wait_done()


def assistant_loop(lang: str, speed_multiplier: float, assistant_name: str) -> None:
    """
    The main loop of the Nova chatbot. Initializes the chatbot and listens for user input to generate responses.
    """
    # Read credentials
    credentials = json.load(open("credentials.json"))

    # Initialize chatgpt with system message
    chatbot = Chatbot(
        config={
            "access_token": credentials["accessToken"],
        },
    )

    instructions = f"Hello! I am {assistant_name}, your GPT-Powered Voice Assistant. Say 'Hello {assistant_name}' followed my a message to talk to me. Say Bye {assistant_name} at any time to finish the conversation"
    system_message = f"Hello! I want you to act as an assistant called {assistant_name} and answer my questions as if we were talking face to face. Don't make the answers too long since they will be read on a microphone, make it as human dialog as possible, being positive, creative and fun. I want you to speak in language code {lang} from now on. Answer this initial message with translating this for the user: {instructions}"

    for data in chatbot.ask(system_message):
        initial_output = data['message']
    synthesize(initial_output, lang=lang, speed_multiplier=speed_multiplier)

    # Start conversation until user preses ESC
    print(
        f"Initializing Nova - Conversation Id {chatbot.conversation_id} - Press ESC for 5 sec after response to end")
    chatbot.change_title(convo_id=chatbot.conversation_id,
                         title="Voice conversation")
    while True:
        audio_data = listen()

        prompt = transcribe(audio_data, lang=lang).lower()

        trigger_end_words = [f'bye', f'adios']
        if any([f'{w} {assistant_name}' in prompt for w in trigger_end_words]):
            break

        activation_words = [f"hello", f"hey", f"okey", f"hola"]

        if any([f'{w} {assistant_name}' in prompt for w in activation_words]):
            for w in activation_words:
                prompt = prompt.replace(f'{w} {assistant_name}', "")

            sentence_counter = 1
            for output in chatbot.ask(prompt):
                sentences = output['message'].split('.')

                if len(sentences) > sentence_counter:
                    synthesize(sentences[sentence_counter - 1], lang=lang, speed_multiplier=speed_multiplier)
                    sentence_counter += 1

            synthesize(sentences[-1], lang=lang, speed_multiplier=speed_multiplier)

    chatbot.delete_conversation(convo_id=chatbot.conversation_id)


if __name__ == "__main__":
    # Add command-line argument parsing
    parser = argparse.ArgumentParser(description="Voice-controlled chatbot")
    parser.add_argument("-l", "--language", default="en", choices=["en", "es"], help="Language code (en, es)")
    parser.add_argument("-s", "--speed_multiplier", type=float, default=1.25, help="Speed multiplier for the assistant's voice output")
    parser.add_argument("-a", "--assistant_name", type=str, default='Nova', help="Assistant name")

    args = parser.parse_args()

    assistant_loop(lang=args.language, speed_multiplier=args.speed_multiplier, assistant_name=args.assistant_name.lower())
