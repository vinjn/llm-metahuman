import gradio as gr


# Code for Task 1
def task1(input_text):
    # Task 1 logic
    return "Task 1 Result: " + input_text


# Code for Task 2
def task2(input_image):
    # Task 2 logic
    return "Task 2 Result"


# interface one
iface1 = gr.Interface(
    fn=task1, inputs="text", outputs="text", title="Multi-Page Interface"
)
# interface two
iface2 = gr.Interface(
    fn=task2, inputs="image", outputs="text", title="Multi-Page Interface"
)

demo = gr.TabbedInterface([iface1, iface2], ["Text-to-text", "image-to-text"])

# Run the interface
demo.launch(share=True)
