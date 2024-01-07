import random
import gradio as gr


def alternatingly_agree(message, history):
    if len(history) % 2 == 0:
        return f"Yes, I do think that '{message}'"
    else:
        return "I don't think so"


count = 0


def textbox_update(chatui_textbox):
    global count
    count += 1
    if count % 10 == 0:
        return "z"
    else:
        return chatui_textbox


if __name__ == "__main__":
    with gr.ChatInterface(alternatingly_agree) as chat_ui:
        chat_ui.textbox.change(
            textbox_update,
            chat_ui.textbox,
            chat_ui.textbox,
            every=1,
            trigger_mode="once",
        )
    chat_ui.launch()
