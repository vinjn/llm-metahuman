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

parser = None

CWD = os.getcwd()
print("CWD:", CWD)

A2F_SERVICE_HEALTHY = False
LIVELINK_SERVICE_HEALTHY = False

client = OpenAI()


def timing_decorator(func):
    def wrapper(*args, **kwargs):
        if not A2F_SERVICE_HEALTHY:
            return None

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
        model=args.tts_model,
        voice=args.tts_voice,
        speed=args.tts_speed,
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
def a2f_post(end_point, data=None, verbose=True):
    global A2F_SERVICE_HEALTHY

    if not A2F_SERVICE_HEALTHY:
        return None

    if verbose:
        print(f"++ {end_point}")
    api_url = f"{args.a2f_url}/{end_point}"
    try:
        response = requests.post(api_url, json=data)

        if response and response.status_code == 200:
            if verbose:
                print(response.json())
            return response.json()
        else:
            if verbose:
                print(f"Error: {response.status_code} - {response.text}")
            return {"Error": response.status_code, "Reason": response.text}
    except Exception as e:
        print(e)
        A2F_SERVICE_HEALTHY = False


@timing_decorator
def a2f_get(end_point, data=None, verbose=True):
    global A2F_SERVICE_HEALTHY

    if not A2F_SERVICE_HEALTHY:
        return None

    if verbose:
        print(f"++ {end_point}")
    api_url = f"{args.a2f_url}/{end_point}"

    try:
        response = requests.get(api_url, json=data)
        if response.status_code == 200:
            if verbose:
                print(response.json())
            return response.json()
        else:
            if verbose:
                print(f"Error: {response.status_code} - {response.text}")
            return {"Error": response.status_code, "Reason": response.text}
    except Exception as e:
        print(e)
        return None


def a2f_player_setlooping(flag=True):
    a2f_post(
        "A2F/Player/SetLooping", {"a2f_player": args.a2f_player_id, "loop_audio": flag}
    )


def a2f_player_play():
    a2f_post("A2F/Player/Play", {"a2f_player": args.a2f_player_id})


def a2f_player_pause():
    a2f_post("A2F/Player/Pause", {"a2f_player": args.a2f_player_id})


def a2f_player_setrootpath(dir_path):
    a2f_post(
        "A2F/Player/SetRootPath",
        {"a2f_player": args.a2f_player_id, "dir_path": dir_path},
    )


def a2f_player_settrack(file_name):
    a2f_post(
        "A2F/Player/SetTrack",
        {"a2f_player": args.a2f_player_id, "file_name": file_name},
    )


def a2f_player_gettracks():
    a2f_post("A2F/Player/GetTracks", {"a2f_player": args.a2f_player_id})


def a2f_player_gettime():
    response = a2f_post("A2F/Player/GetTime", {"a2f_player": args.a2f_player_id}, False)
    if response and response["status"] == "OK":
        return response["result"]
    else:
        return 0


def a2f_player_getrange():
    response = a2f_post(
        "A2F/Player/GetRange", {"a2f_player": args.a2f_player_id}, False
    )
    if response and response["status"] == "OK":
        return response["result"]["work"]
    else:
        return (0, 0)


def a2f_generatekeys():
    a2f_post("A2F/A2E/GenerateKeys", {"a2f_instance": args.a2f_instance_id})


def a2f_ActivateStreamLivelink(flag):
    a2f_post(
        "A2F/Exporter/ActivateStreamLivelink",
        {"node_path": args.a2f_livelink_id, "value": flag},
    )


def a2f_IsStreamLivelinkConnected():
    response = a2f_post(
        "A2F/Exporter/IsStreamLivelinkConnected",
        {"node_path": args.a2f_livelink_id},
    )
    if response and response["status"] == "OK":
        return response["result"]
    else:
        return False


def a2f_enable_audio_stream(flag):
    a2f_post(
        "A2F/Exporter/SetStreamLivelinkSettings",
        {"node_path": args.a2f_livelink_id, "values": {"enable_audio_stream": flag}},
    )


def a2f_set_livelink_ports(
    livelink_host,
    livelink_subject,
    livelink_port,
    audio_port,
):
    a2f_post(
        "A2F/Exporter/SetStreamLivelinkSettings",
        {
            "node_path": args.a2f_livelink_id,
            "values": {
                "livelink_host": livelink_host,
                "livelink_subject": livelink_subject,
                "livelink_port": livelink_port,
                "audio_port": audio_port,
            },
        },
    )


def a2f_get_preprocessing():
    response = a2f_post(
        "A2F/PRE/GetSettings",
        {"a2f_instance": args.a2f_instance_id},
    )
    if response and response["status"] == "OK":
        return response["result"]
    else:
        return {}


def a2f_set_preprocessing(settings):
    settings["a2f_instance"] = args.a2f_instance_id
    a2f_post("A2F/PRE/SetSettings", settings)


def a2f_get_postprocessing():
    response = a2f_post(
        "A2F/POST/GetSettings",
        {"a2f_instance": args.a2f_instance_id},
    )
    if response and response["status"] == "OK":
        return response["result"]
    else:
        return {}


def a2f_set_postprocessing(settings):
    a2f_post(
        "A2F/POST/SetSettings",
        {"a2f_instance": args.a2f_instance_id, "settings": settings},
    )


def a2f_setup():
    global A2F_SERVICE_HEALTHY, LIVELINK_SERVICE_HEALTHY
    # try it :)
    A2F_SERVICE_HEALTHY = True

    a2f_ActivateStreamLivelink(True)
    LIVELINK_SERVICE_HEALTHY = a2f_IsStreamLivelinkConnected()

    a2f_player_setrootpath(CWD)
    a2f_player_setlooping(False)
    a2f_enable_audio_stream(True)

    a2f_set_livelink_ports(
        args.livelink_host, args.livelink_subject, args.livelink_port, args.audio_port
    )

    pre_settings = a2f_get_preprocessing()
    pre_settings["prediction_delay"] = 0
    pre_settings["blink_interval"] = 1.5
    a2f_set_preprocessing(pre_settings)

    post_settings = a2f_get_postprocessing()
    post_settings["skin_strength"] = 1.3
    a2f_set_postprocessing(post_settings)


files_to_delete = []


@timing_decorator
def run_pipeline(answer):
    global stop_current_a2f_play
    # print(answer)
    mp3_file = text_to_mp3(answer)
    wav_file = mp3_to_wav(mp3_file)
    duration = a2f_player_getrange()[1]
    position = a2f_player_gettime()
    while position > 0 and position < duration:
        print(position)
        if stop_current_a2f_play:
            print("stop_current_a2f_play")
            stop_current_a2f_play = False
            return

        time.sleep(1)
        position = a2f_player_gettime()
        print("z")
    a2f_player_setrootpath(CWD)
    a2f_player_settrack(wav_file)
    # a2f_generatekeys()

    a2f_player_play()

    for file in files_to_delete:
        try:
            os.remove(file)
        except Exception:
            pass
    files_to_delete.clear()

    files_to_delete.append(mp3_file)
    files_to_delete.append(wav_file)


@timing_decorator
def get_completion(chat_history):
    response = completion(
        model=args.chat_model,
        messages=chat_history,
        api_base=args.chat_url,
        stream=args.chat_streaming,
    )

    print(response)
    return response


q = queue.Queue()
cleanup_queue = False
stop_current_a2f_play = False


def pipeline_worker():
    while True:
        print("--------------------------")
        global cleanup_queue
        global stop_current_a2f_play
        if cleanup_queue:
            while not q.empty():
                item = q.get()
                q.task_done()

                if item == "cleanup_queue_token":
                    break
            cleanup_queue = False
            stop_current_a2f_play = True

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
        yield f"A2F running: {A2F_SERVICE_HEALTHY}\nLive Link running: {LIVELINK_SERVICE_HEALTHY}"
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

    if message == "stop":
        global cleanup_queue
        cleanup_queue = True
        q.put("cleanup_queue_token")
        yield "stopped"
        return

    history_openai_format = []
    for human, assistant in history:
        history_openai_format.append({"role": "user", "content": human})
        history_openai_format.append({"role": "assistant", "content": assistant})
    history_openai_format.append({"role": "user", "content": message})

    start_time = time.time()
    response = get_completion(history_openai_format)
    yield ".."

    # global cleanup_queue
    # cleanup_queue = True
    # q.put("cleanup_queue_token")

    if args.chat_streaming:
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
            # print(
            #     f"Message {chunk_time:.2f} s after request: {chunk_message}"
            # )  # print the delay and text
            print(chunk_message)

            if chunk_message:
                chunk_message = chunk_message.rstrip("\n")

            if chunk_message in [".", "!", "?", "。", "!", "？"]:
                # if not chunk_message or "\n" in chunk_message:
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
    import argparse

    parser = argparse.ArgumentParser(description="llm.py arguments")

    parser.add_argument("--chat_engine", choices=["gpt", "llama2"], default="gpt")
    parser.add_argument(
        "--chat_model", default=None, help="https://docs.litellm.ai/docs/providers"
    )
    parser.add_argument("--chat_url", default=None)

    parser.add_argument("--chat_streaming", default=True)

    parser.add_argument("--a2f_url", default="http://localhost:8011")
    parser.add_argument("--a2f_instance_id", default="/World/audio2face/CoreFullface")
    parser.add_argument("--a2f_player_id", default="/World/audio2face/Player")
    parser.add_argument("--a2f_livelink_id", default="/World/audio2face/StreamLivelink")

    parser.add_argument("--tts_model", choices=["tts-1", "tts-1-hd"], default="tts-1")
    parser.add_argument("--tts_speed", type=float, default=1.1)

    parser.add_argument("--livelink_host", default="localhost")
    parser.add_argument("--livelink_subject", default="Audio2Face")
    parser.add_argument("--livelink_port", type=int, default=12030)
    parser.add_argument("--audio_port", type=int, default=12031)

    parser.add_argument(
        "--tts_voice",
        choices=["alloy", "echo", "fable", "onyx", "nova", "shimmer"],
        default="nova",
        help="https://platform.openai.com/docs/guides/text-to-speech",
    )

    args = parser.parse_args()

    if not args.chat_model:
        if args.chat_engine == "gpt":
            args.chat_model = args.chat_model or "gpt-3.5-turbo"
        elif args.chat_engine == "llama2":
            args.chat_model = args.chat_model or "ollama/llama2"
            args.chat_url = args.chat_url or "http://localhost:11434"

    threading.Thread(target=pipeline_worker, daemon=True).start()

    a2f_setup()
    gr.ChatInterface(predict).queue().launch()

    q.join()
