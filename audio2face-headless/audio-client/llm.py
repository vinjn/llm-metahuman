from openai import OpenAI
from pydub import AudioSegment
import gradio as gr
import requests
import os
from litellm import completion
import time

# XXX: increase requests speed
# https://stackoverflow.com/a/72440253
requests.packages.urllib3.util.connection.HAS_IPV6 = False

CWD = os.getcwd()
print("CWD:", CWD)

# Chat
# https://docs.litellm.ai/docs/providers
chat_model = "gpt"
# chat_model = "llama2"
CHAT_MODEL_NAME = "gpt-3.5-turbo"
CHAT_BASE_URL = None

if chat_model == "llama2":
    CHAT_MODEL_NAME = "ollama/llama2"
    CHAT_BASE_URL = "http://localhost:11434"

# A2F
A2F_BASE_URL = "http://localhost:8011"
A2F_INSTANCE = "/World/audio2face/CoreFullface"
A2F_PLAYER = "/World/audio2face/Player"
A2F_LIVELINK_NODE = "/World/audio2face/StreamLivelink"

# TTS
voice = "nova"
model = "tts-1-hd"

voice = "alloy"
model = "tts-1"

voice = "fable"

client = OpenAI()


def timing_decorator(func):
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        elapsed_time = end_time - start_time
        print(f"{func.__name__} cost: {elapsed_time:.2f} seconds.")
        return result

    return wrapper


@timing_decorator
def text_to_mp3(text):
    response = client.audio.speech.create(
        model=model,
        voice=voice,
        input=text,
    )
    response.stream_to_file(f"{voice}-output.mp3")

    return f"{voice}-output.mp3"


@timing_decorator
def mp3_to_wav(mp3_filename):
    sound = AudioSegment.from_mp3(mp3_filename)
    sound = sound.set_frame_rate(22050)
    sound.export(f"{voice}-output.wav", format="wav")

    return f"{voice}-output.wav"


@timing_decorator
def a2f_post(end_point, data=None):
    print(f"[[ {end_point}")
    api_url = f"{A2F_BASE_URL}/{end_point}"
    response = requests.post(api_url, json=data)
    if response.status_code == 200:
        print(response.json())
    else:
        print(f"Error: {response.status_code} - {response.text}")
    print(f"]] {end_point}")


@timing_decorator
def a2f_get(end_point, data=None):
    api_url = f"{A2F_BASE_URL}/{end_point}"
    response = requests.get(api_url, json=data)
    if response.status_code == 200:
        print(response.json())
    else:
        print(f"Error: {response.status_code} - {response.text}")


def a2f_player_setlooping(flag=True):
    a2f_post("A2F/Player/SetLooping", {"a2f_player": A2F_PLAYER, "loop_audio": flag})


def a2f_player_play():
    a2f_post("A2F/Player/Play", {"a2f_player": A2F_PLAYER})


def a2f_player_pause():
    a2f_post("A2F/Player/Pause", {"a2f_player": A2F_PLAYER})


def a2f_player_setrootpath(dir_path):
    a2f_post("A2F/Player/SetRootPath", {"a2f_player": A2F_PLAYER, "dir_path": dir_path})


def a2f_player_settrack(file_name):
    a2f_post("A2F/Player/SetTrack", {"a2f_player": A2F_PLAYER, "file_name": file_name})


def a2f_player_gettracks():
    a2f_post("A2F/Player/GetTracks", {"a2f_player": A2F_PLAYER})


def a2f_generatekeys():
    a2f_post("A2F/A2E/GenerateKeys", {"a2f_instance": A2F_INSTANCE})


def a2f_ActivateStreamLivelink(flag=True):
    a2f_post(
        "A2F/Exporter/ActivateStreamLivelink",
        {"node_path": A2F_LIVELINK_NODE, "value": flag},
    )


def a2f_enable_audio_stream(flag=True):
    a2f_post(
        "A2F/Exporter/SetStreamLivelinkSettings",
        {"node_path": A2F_LIVELINK_NODE, "values": {"enable_audio_stream": flag}},
    )


def a2f_setup():
    a2f_player_setrootpath(CWD)
    a2f_ActivateStreamLivelink()
    a2f_player_setlooping(False)
    a2f_enable_audio_stream(True)


def a2f_test():
    a2f_player_test()


@timing_decorator
def get_completion(chat_history):
    response = completion(
        model=CHAT_MODEL_NAME,
        messages=chat_history,
        api_base=CHAT_BASE_URL,
    )

    # response = client.chat.completions.create(
    #     model="gpt-3.5-turbo",
    #     messages=history_openai_format,
    #     temperature=1.0,
    #     stream=False,
    # )

    print(response)
    return response


def predict(message, history):
    print("==========================")
    if message == "setup":
        a2f_setup()
        yield "A2F setup"
        return

    if message == "ping":
        a2f_post("")
        a2f_get("")
        yield "A2F ping"
        return

    if message == "redo":
        a2f_player_play()
        yield "A2F redo"
        return

    history_openai_format = []
    for human, assistant in history:
        history_openai_format.append({"role": "user", "content": human})
        history_openai_format.append({"role": "assistant", "content": assistant})
    history_openai_format.append({"role": "user", "content": message})

    response = get_completion(history_openai_format)
    yield ".."

    if len(response.choices[0].message.content) != 0:
        answer = response.choices[0].message.content
        yield answer

        mp3_file = text_to_mp3(answer)
        wav_file = mp3_to_wav(mp3_file)
        yield "....\n" + answer

        a2f_player_settrack(wav_file)
        yield "......\n" + answer

        a2f_generatekeys()
        yield "........\n" + answer

        a2f_player_play()
        yield "..........\n" + answer


if __name__ == "__main__":
    a2f_setup()
    gr.ChatInterface(predict).queue().launch()
    # a2f_player_pause()
