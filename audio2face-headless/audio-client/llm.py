from openai import OpenAI
from pydub import AudioSegment
import gradio as gr
import requests
import os
from litellm import completion
import time
import threading
import queue

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
CHAT_STREAMING = True

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

voice = "shimmer"

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
    timestamp = time.time()
    mp3_filename = f"{timestamp}.mp3"
    response.stream_to_file(mp3_filename)

    return mp3_filename


@timing_decorator
def mp3_to_wav(mp3_filename):
    sound = AudioSegment.from_mp3(mp3_filename)
    sound = sound.set_frame_rate(22050)
    wav_filename = f"{mp3_filename}.wav"
    sound.export(wav_filename, format="wav")

    return wav_filename


@timing_decorator
def a2f_post(end_point, data=None):
    print(f"++ {end_point}")
    api_url = f"{A2F_BASE_URL}/{end_point}"
    response = requests.post(api_url, json=data)
    if response.status_code == 200:
        print(response.json())
        return response.json()
    else:
        print(f"Error: {response.status_code} - {response.text}")
        return {"Error": response.status_code, "Reason": response.text}


@timing_decorator
def a2f_get(end_point, data=None):
    print(f"++ {end_point}")
    api_url = f"{A2F_BASE_URL}/{end_point}"
    response = requests.get(api_url, json=data)
    if response.status_code == 200:
        print(response.json())
        return response.json()
    else:
        print(f"Error: {response.status_code} - {response.text}")
        return {"Error": response.status_code, "Reason": response.text}


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


def a2f_player_gettime():
    response = a2f_post("A2F/Player/GetTime", {"a2f_player": A2F_PLAYER})
    if response["status"] == "OK":
        return response["result"]
    else:
        return 0


def a2f_player_getrange():
    response = a2f_post("A2F/Player/GetRange", {"a2f_player": A2F_PLAYER})
    if response["status"] == "OK":
        return response["result"]["work"]
    else:
        return (0, 0)


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


def a2f_get_preprocessing():
    response = a2f_post(
        "A2F/PRE/GetSettings",
        {"a2f_instance": A2F_INSTANCE},
    )
    if response["status"] == "OK":
        return response["result"]
    else:
        return {}


def a2f_set_preprocessing(settings):
    settings["a2f_instance"] = A2F_INSTANCE
    a2f_post("A2F/PRE/SetSettings", settings)


def a2f_get_postprocessing():
    response = a2f_post(
        "A2F/POST/GetSettings",
        {"a2f_instance": A2F_INSTANCE},
    )
    if response["status"] == "OK":
        return response["result"]
    else:
        return {}


def a2f_set_postprocessing(settings):
    a2f_post(
        "A2F/POST/SetSettings", {"a2f_instance": A2F_INSTANCE, "settings": settings}
    )


def a2f_setup():
    a2f_player_setrootpath(CWD)
    a2f_ActivateStreamLivelink()
    a2f_player_setlooping(False)
    a2f_enable_audio_stream(True)

    pre_settings = a2f_get_preprocessing()
    pre_settings["prediction_delay"] = 0
    pre_settings["blink_interval"] = 1.5
    a2f_set_preprocessing(pre_settings)

    post_settings = a2f_get_postprocessing()
    post_settings["skin_strength"] = 1.3
    a2f_set_postprocessing(post_settings)


@timing_decorator
def run_pipeline(answer):
    global stop_current_a2f
    print(answer)
    mp3_file = text_to_mp3(answer)
    wav_file = mp3_to_wav(mp3_file)
    duration = a2f_player_getrange()[1]
    position = a2f_player_gettime()
    while position > 0 and position < duration:
        if stop_current_a2f:
            stop_current_a2f = False
            break
        time.sleep(1)
        position = a2f_player_gettime()
        print("z")
    # a2f_player_setrootpath(CWD)
    a2f_player_settrack(wav_file)
    # a2f_generatekeys()

    time.sleep(1)
    a2f_player_play()


@timing_decorator
def get_completion(chat_history):
    response = completion(
        model=CHAT_MODEL_NAME,
        messages=chat_history,
        api_base=CHAT_BASE_URL,
        stream=CHAT_STREAMING,
    )

    print(response)
    return response


q = queue.Queue()
cleanup_queue = False
stop_current_a2f = False


def pipeline_worker():
    while True:
        print("--------------------------")
        global cleanup_queue
        global stop_current_a2f
        if cleanup_queue:
            while not q.empty():
                item = q.get()
                q.task_done()

                if item == "cleanup_queue_token":
                    break
            cleanup_queue = False
            stop_current_a2f = True

        item = q.get()
        if item == "cleanup_queue_token":
            continue

        print(f"Working on {item}")
        run_pipeline(item)
        print(f"Finished {item}")
        q.task_done()


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

    start_time = time.time()
    response = get_completion(history_openai_format)
    yield ".."

    global cleanup_queue
    cleanup_queue = True
    q.put("cleanup_queue_token")

    if CHAT_STREAMING:
        # create variables to collect the stream of chunks
        UNUSED_collected_chunks = []
        collected_messages = []
        complete_sentences = ""
        # iterate through the stream of events
        for chunk in response:
            chunk_time = (
                time.time() - start_time
            )  # calculate the time delay of the chunk
            UNUSED_collected_chunks.append(chunk)  # save the event response
            chunk_message = chunk.choices[0].delta.content  # extract the message

            collected_messages.append(chunk_message)  # save the message
            print(
                f"Message received {chunk_time:.2f} seconds after request: {chunk_message}"
            )  # print the delay and text

            # if chunk_message in [".", "!", "?", "。", "!", "？"]:
            if not chunk_message or "\n" in chunk_message:
                one_sentence = "".join([m for m in collected_messages if m is not None])
                if len(one_sentence) < 10:
                    # ignore short sentences
                    continue
                collected_messages = []
                complete_sentences += one_sentence
                q.put(one_sentence)
                # run_pipeline(one_sentence)
                yield complete_sentences

        # print the time delay and text received
        # print(f"Full response received {chunk_time:.2f} seconds after request")
        # # clean None in collected_messages
        # collected_messages = [m for m in collected_messages if m is not None]
        # full_reply_content = "".join([m for m in collected_messages])
        # print(f"Full conversation received: {full_reply_content}")
        # yield full_reply_content
    else:
        if len(response.choices[0].message.content) == 0:
            return

        answer = response.choices[0].message.content
        yield answer

        run_pipeline(answer)


if __name__ == "__main__":
    threading.Thread(target=pipeline_worker, daemon=True).start()

    a2f_setup()
    gr.ChatInterface(predict).queue().launch()
    # a2f_player_pause()

    q.join()
