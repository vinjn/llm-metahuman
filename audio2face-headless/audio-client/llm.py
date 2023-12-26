from openai import OpenAI
from pydub import AudioSegment
import gradio as gr
import requests
import os

CWD = os.getcwd()
print("CWD:", CWD)

A2F_BASE_URL = "http://localhost:8011"
A2F_INSTANCE = "/World/audio2face/CoreFullface"
A2F_PLAYER = "/World/audio2face/Player"
A2F_LIVELINK_NODE = "/World/audio2face/StreamLivelink"

client = OpenAI()


def text_to_audio(text):
    voice = "nova"
    model = "tts-1-hd"
    voice = "alloy"

    print("speech request")
    response = client.audio.speech.create(
        model=model,
        voice=voice,
        input=text,
    )
    print("speech response")

    response.stream_to_file(f"{voice}-output.mp3")

    print("wav request")
    sound = AudioSegment.from_mp3(f"{voice}-output.mp3")
    sound = sound.set_frame_rate(22050)
    sound.export(f"{voice}-output.wav", format="wav")
    print("wav response")

    return f"{voice}-output.wav"


def a2f_post(end_point, data=None):
    api_url = f"{A2F_BASE_URL}/{end_point}"
    response = requests.post(api_url, json=data)
    if response.status_code == 200:
        print(response.json())
    else:
        print(f"Error: {response.status_code} - {response.text}")


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


def a2f_generatekeys(file_name):
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


def predict(message, history):
    if message == "setup":
        a2f_setup()
        yield "A2F setup"
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

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=history_openai_format,
        temperature=1.0,
        stream=False,
    )
    yield "chat completed"

    if len(response.choices[0].message.content) != 0:
        answer = response.choices[0].message.content
        audio_file = text_to_audio(answer)
        yield "audio completed"

        a2f_player_settrack(audio_file)
        yield "a2f_player_settrack"

        a2f_player_play()
        yield "a2f_player_play"

        yield answer


gr.ChatInterface(predict).queue().launch()

a2f_player_pause()
