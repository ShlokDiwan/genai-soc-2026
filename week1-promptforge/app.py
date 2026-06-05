import gradio as gr
import os
import json
from groq import Groq
from personas import PERSONAS
from dotenv import load_dotenv

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def build_messages(persona, query):
    messages = [
        {
            "role": "system",
            "content": persona["system_prompt"]
        }
    ]

    for ex in persona["few_shot_examples"]:
        messages.append(
            {
                "role": "user",
                "content": ex["user"]
            }
        )

        messages.append(
            {
                "role": "assistant",
                "content": ex["assistant"]
            }
        )

    messages.append(
        {
            "role": "user",
            "content": query
        }
    )

    return messages


def format_json_response(response):
    try:
        parsed = json.loads(response)

        return f"""
### Severity
{parsed.get("severity", "Unknown")}

### Issues
{chr(10).join(f"- {i}" for i in parsed.get("issues", []))}

### Suggestions
{chr(10).join(f"- {s}" for s in parsed.get("suggestions", []))}
"""
    except Exception:
        return "Could not parse JSON\n\n" + response


def chat(message, history, mode, temperature):
    persona = PERSONAS[mode]

    messages = build_messages(
        persona,
        message
    )

    stream = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=messages,
        temperature=temperature,
        stream=True
    )

    full_response = ""

    for chunk in stream:
        token = chunk.choices[0].delta.content or ""
        full_response += token
        yield full_response

    if mode == "Code Reviewer":
        yield format_json_response(full_response)


def update_prompt(mode):
    return PERSONAS[mode]["system_prompt"]


with gr.Blocks() as demo:

    gr.Markdown("# PromptForge")

    mode = gr.Dropdown(
        choices=list(PERSONAS.keys()),
        value=list(PERSONAS.keys())[0],
        label="Mode"
    )

    temperature = gr.Slider(
        0,
        1.5,
        value=0.7,
        step=0.1,
        label="Temperature"
    )

    with gr.Accordion(
        "Active System Prompt",
        open=False
    ):
        prompt_display = gr.Textbox(
            value=PERSONAS[list(PERSONAS.keys())[0]]["system_prompt"],
            lines=6,
            interactive=False
        )

    mode.change(
        update_prompt,
        inputs=mode,
        outputs=prompt_display
    )

    gr.ChatInterface(
        fn=chat,
        additional_inputs=[
            mode,
            temperature
        ]
    )

if __name__ == "__main__":
    demo.launch()