from openai import OpenAI
from pydub import AudioSegment
import gradio as gr
import requests
import os
from litellm import completion
import time
import threading
import queue
import gradio_client as gc


# XXX: increase requests speed
# https://stackoverflow.com/a/72440253
requests.packages.urllib3.util.connection.HAS_IPV6 = False

args = None

CWD = os.getcwd()
print("CWD:", CWD)

VOICE_ACTORS = ["nova", "alloy", "echo", "fable", "onyx", "shimmer"]


def timing_decorator(func):
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        elapsed_time = end_time - start_time
        print(f"{func.__name__} cost: {elapsed_time:.2f} seconds.")
        return result

    return wrapper


class A2fInstance:
    files_to_delete = []
    instaces = []

    def __init__(self, index) -> None:
        self.SERVICE_HEALTHY = False
        self.LIVELINK_SERVICE_HEALTHY = False
        self.index = index

    @timing_decorator
    def post(self, end_point, data=None, verbose=True):
        if not self.SERVICE_HEALTHY:
            return None

        if verbose:
            print(f"++ {end_point}")
        api_url = f"{self.base_url}/{end_point}"
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
            self.SERVICE_HEALTHY = False
            return None

    @timing_decorator
    def get(self, end_point, data=None, verbose=True):
        if not self.SERVICE_HEALTHY:
            return None

        if verbose:
            print(f"++ {end_point}")
        api_url = f"{self.base_url}/{end_point}"

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
            self.SERVICE_HEALTHY = False
            return None

    def player_setlooping(self, flag=True):
        self.post(
            "A2F/Player/SetLooping",
            {"a2f_player": args.a2f_player_id, "loop_audio": flag},
        )

    def player_play(self):
        self.post("A2F/Player/Play", {"a2f_player": args.a2f_player_id})

    def player_pause(self):
        self.post("A2F/Player/Pause", {"a2f_player": args.a2f_player_id})

    def player_setrootpath(self, dir_path):
        self.post(
            "A2F/Player/SetRootPath",
            {"a2f_player": args.a2f_player_id, "dir_path": dir_path},
        )

    def player_settrack(self, file_name):
        self.post(
            "A2F/Player/SetTrack",
            {"a2f_player": args.a2f_player_id, "file_name": file_name},
        )

    def player_gettracks(self):
        self.post("A2F/Player/GetTracks", {"a2f_player": args.a2f_player_id})

    def player_gettime(self):
        response = self.post(
            "A2F/Player/GetTime", {"a2f_player": args.a2f_player_id}, False
        )
        if response and response["status"] == "OK":
            return response["result"]
        else:
            return 0

    def player_getrange(self):
        response = self.post(
            "A2F/Player/GetRange", {"a2f_player": args.a2f_player_id}, False
        )
        if response and response["status"] == "OK":
            return response["result"]["work"]
        else:
            return (0, 0)

    def generatekeys(self):
        self.post("A2F/A2E/GenerateKeys", {"a2f_instance": args.a2f_instance_id})

    def ActivateStreamLivelink(self, flag):
        self.post(
            "A2F/Exporter/ActivateStreamLivelink",
            {"node_path": args.a2f_livelink_id, "value": flag},
        )

    def IsStreamLivelinkConnected(self):
        response = self.post(
            "A2F/Exporter/IsStreamLivelinkConnected",
            {"node_path": args.a2f_livelink_id},
        )
        if response and response["status"] == "OK":
            return response["result"]
        else:
            return False

    def enable_audio_stream(self, flag):
        self.post(
            "A2F/Exporter/SetStreamLivelinkSettings",
            {
                "node_path": args.a2f_livelink_id,
                "values": {"enable_audio_stream": flag},
            },
        )

    def set_livelink_ports(
        self,
        livelink_host,
        livelink_subject,
        livelink_port,
        audio_port,
    ):
        self.post(
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

    def get_preprocessing(self):
        response = self.post(
            "A2F/PRE/GetSettings",
            {"a2f_instance": args.a2f_instance_id},
        )
        if response and response["status"] == "OK":
            return response["result"]
        else:
            return {}

    def set_preprocessing(self, settings):
        settings["a2f_instance"] = args.a2f_instance_id
        self.post("A2F/PRE/SetSettings", settings)

    def get_postprocessing(self):
        response = self.post(
            "A2F/POST/GetSettings",
            {"a2f_instance": args.a2f_instance_id},
        )
        if response and response["status"] == "OK":
            return response["result"]
        else:
            return {}

    def set_postprocessing(self, settings):
        self.post(
            "A2F/POST/SetSettings",
            {"a2f_instance": args.a2f_instance_id, "settings": settings},
        )

    def setup(self):
        self.base_url = f"http://{args.a2f_host}:{args.a2f_port+self.index}"
        self.tts_voice = args.tts_voice
        if self.index > 1:
            # TODO: make it elegant
            self.tts_voice = VOICE_ACTORS[self.index % len(VOICE_ACTORS)]

        # always ping SERVICE_HEALTHY again in setup()
        self.SERVICE_HEALTHY = True

        self.ActivateStreamLivelink(True)
        if not self.SERVICE_HEALTHY:
            return

        self.player_setrootpath(CWD)
        self.player_setlooping(False)

        self.LIVELINK_SERVICE_HEALTHY = self.IsStreamLivelinkConnected()
        if not self.LIVELINK_SERVICE_HEALTHY:
            return

        self.enable_audio_stream(True)

        self.set_livelink_ports(
            args.livelink_host,
            args.livelink_subject,
            args.livelink_port + 10 * self.index,
            args.audio_port + 10 * self.index,
        )

        pre_settings = self.get_preprocessing()
        pre_settings["prediction_delay"] = 0
        pre_settings["blink_interval"] = 1.5
        self.set_preprocessing(pre_settings)

        post_settings = self.get_postprocessing()
        post_settings["skin_strength"] = 1.3
        self.set_postprocessing(post_settings)


A2fInstance.instaces = []
openai_client = OpenAI()
gc_client: gc.Client = None
chat_ui: gr.ChatInterface = None


def run_single_pipeline(a2f, answer):
    global stop_current_a2f_play

    # print(answer)
    mp3_file = text_to_mp3(answer, a2f.tts_voice)
    wav_file = mp3_to_wav(mp3_file)
    duration = a2f.player_getrange()[1]
    position = a2f.player_gettime()
    while position > 0 and position < duration:
        print(position)
        if stop_current_a2f_play:
            print("stop_current_a2f_play")
            stop_current_a2f_play = False
            return

        time.sleep(1)
        position = a2f.player_gettime()
        print("z")
    a2f.player_setrootpath(CWD)
    a2f.player_settrack(wav_file)
    # a2f_generatekeys()

    a2f.player_play()

    for file in A2fInstance.files_to_delete:
        try:
            os.remove(file)
        except Exception:
            pass
    A2fInstance.files_to_delete.clear()

    A2fInstance.files_to_delete.append(mp3_file)
    A2fInstance.files_to_delete.append(wav_file)


@timing_decorator
def run_pipeline(answer):
    if args.a2f_instance_count == 1:
        run_single_pipeline(A2fInstance.instaces[0], answer)
        return

    for a2f in A2fInstance.instaces:
        if not a2f.SERVICE_HEALTHY:
            return

        print("z")


@timing_decorator
def text_to_mp3(text, voice):
    response = openai_client.audio.speech.create(
        model=args.tts_model,
        voice=voice,
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
def get_completion(chat_history):
    response = completion(
        model=args.llm_model,
        messages=chat_history,
        api_base=args.llm_url,
        stream=args.llm_streaming,
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

        print(f"Begin: {item}")
        run_pipeline(item)
        print(f"End: {item}")
        q.task_done()


def talk_to_peer(message):
    if not gc_client:
        return

    result = gc_client.predict(
        message, api_name="/chat"  # str  in 'Message' Textbox component
    )
    print(f"from peer: {result}")

    # chat_ui.textbox.submit(None, [result, result])
    # chat_ui.textbox.submit()


def predict(message, history):
    print("==========================")
    if message == "setup":
        str = ""
        for a2f in A2fInstance.instaces:
            a2f.setup()
            str += f"A2F running: {a2f.SERVICE_HEALTHY}\nLive Link running: {a2f.LIVELINK_SERVICE_HEALTHY}"
        yield str
        return

    if message == "ping":
        for a2f in A2fInstance.instaces:
            a2f.post("")
            a2f.get("")
        yield "A2F ping"
        return

    if message == "redo":
        for a2f in A2fInstance.instaces:
            a2f.player_play()
        yield "A2F redo"
        return

    if message == "stop":
        global cleanup_queue
        cleanup_queue = True
        q.put("cleanup_queue_token")
        yield "stopped"
        return

    if message.startswith("peer"):
        items = message.split()
        if len(items) >= 2:
            gradio_port = int(items[1])
            # TODO: support non localhost
            args.gradio_peer_url = f"http://{args.gradio_host}:{gradio_port}/"
            global gc_client
            gc_client = gc.Client(args.gradio_peer_url)

            yield f"I will chat with another llm-metahuman: {args.gradio_peer_url}"
        return

    history_openai_format = []
    for human, assistant in history:
        history_openai_format.append({"role": "user", "content": human})
        history_openai_format.append({"role": "assistant", "content": assistant})
    history_openai_format.append({"role": "user", "content": message})

    # start_time = time.time()
    response = get_completion(history_openai_format)
    yield ".."

    # global cleanup_queue
    # cleanup_queue = True
    # q.put("cleanup_queue_token")

    if args.llm_streaming:
        # create variables to collect the stream of chunks
        UNUSED_collected_chunks = []
        collected_messages = []
        complete_sentences = ""
        # iterate through the stream of events
        for chunk in response:
            # chunk_time = (
            #     time.time() - start_time
            # )  # calculate the time delay of the chunk
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

                talk_to_peer(one_sentence)

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


def main():
    import argparse

    parser = argparse.ArgumentParser(description="llm.py arguments")

    # gradio settings
    parser.add_argument("--a2f_instance_count", type=int, default=1)
    parser.add_argument("--gradio_host", default="localhost")
    parser.add_argument("--gradio_port", type=int, default=7860)
    parser.add_argument(
        "--gradio_peer_url",
        default=None,
        help="the gradio peer that this gradio instance will chat with. Default value is None, which means chat with a human.",
    )

    # llm / litellm settings
    parser.add_argument("--llm_engine", default="gpt", choices=["gpt", "llama2"])
    parser.add_argument(
        "--llm_model", default=None, help="https://docs.litellm.ai/docs/providers"
    )
    parser.add_argument("--llm_url", default=None)
    parser.add_argument(
        "--llm_streaming", default=True, action=argparse.BooleanOptionalAction
    )

    # audio2face settings
    parser.add_argument("--a2f_host", default="localhost")
    parser.add_argument("--a2f_port", default=8011, type=int)
    parser.add_argument("--a2f_instance_id", default="/World/audio2face/CoreFullface")
    parser.add_argument("--a2f_player_id", default="/World/audio2face/Player")
    parser.add_argument("--a2f_livelink_id", default="/World/audio2face/StreamLivelink")

    # tts settings
    parser.add_argument("--tts_model", default="tts-1", choices=["tts-1", "tts-1-hd"])
    parser.add_argument("--tts_speed", default=1.1, type=float)

    # livelink settings
    parser.add_argument("--livelink_host", default="localhost")
    parser.add_argument("--livelink_port", default=12030, type=int)
    parser.add_argument("--livelink_subject", default="Audio2Face")
    parser.add_argument("--livelink_audio_port", default=12031, type=int)

    parser.add_argument(
        "--tts_voice",
        default="nova",
        choices=VOICE_ACTORS,
        help="https://platform.openai.com/docs/guides/text-to-speech",
    )

    global args
    args = parser.parse_args()

    if not args.llm_model:
        if args.llm_engine == "gpt":
            args.llm_model = args.llm_model or "gpt-3.5-turbo"
        elif args.llm_engine == "llama2":
            args.llm_model = args.llm_model or "ollama/llama2"
            args.llm_url = args.llm_url or "http://localhost:11434"

    threading.Thread(target=pipeline_worker, daemon=True).start()

    for i in range(args.a2f_instance_count):
        a2f = A2fInstance(i)
        a2f.setup()
        A2fInstance.instaces.append(a2f)

    global chat_ui
    chat_ui = gr.ChatInterface(
        predict,
        title=f"llm-metahuman @{args.gradio_port}",
        examples=["hello", "tell me 3 jokes", "what's the meaning of life?"],
    )

    chat_ui.queue().launch(server_name=args.gradio_host, server_port=args.gradio_port)

    q.join()


if __name__ == "__main__":
    main()
