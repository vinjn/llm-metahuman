import gradio as gr


def task1(input_text):
    return "Task 1 Result: " + input_text


def task2(input_image):
    return "Task 2 Result"


def task3(input_image):
    return "Task 2 Result"


# interface one
iface1 = gr.Interface(
    fn=task1, inputs="text", outputs="text", title="Multi-Page Interface"
)
# interface two
iface2 = gr.Interface(
    fn=task2, inputs="image", outputs="text", title="Multi-Page Interface"
)

tts_examples = [
    "I love learning machine learning",
    "How do you do?",
]


tts_demo = gr.load(
    "huggingface/facebook/fastspeech2-en-ljspeech",
    title=None,
    examples=tts_examples,
    description="Give me something to say!",
    cache_examples=False,
)

stt_demo = gr.load(
    "huggingface/facebook/wav2vec2-base-960h",
    title=None,
    inputs="mic",
    description="Let me try to guess what you're saying!",
)


demo = gr.TabbedInterface(
    [iface1, iface2, tts_demo, stt_demo],
    ["Text-to-text", "image-to-text", "Text-to-speech", "Speech-to-text"],
)

# Run the interface
demo.launch(share=True)
