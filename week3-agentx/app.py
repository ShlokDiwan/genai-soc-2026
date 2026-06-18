import uuid
import gradio as gr
from agent import run_agent_with_trace

def chat(message, history, session_id, trace_display):
    if history is None:
        history = []

    if not message.strip():
        return history, session_id, trace_display

    ans, trace = run_agent_with_trace(message, session_id)

    history.append(
        {
            "role": "user",
            "content": message
        }
    )

    history.append(
        {
            "role": "assistant",
            "content": ans
        }
    )

    return history, session_id, trace

with gr.Blocks(title="AgentX - Your research agent") as demo:
    session_id = gr.State(str(uuid.uuid4()))
    gr.Markdown("#AgentX\nA research agent with web access and memory.")
    chatbot=gr.Chatbot(
        height=420,
        label="Convo"
    )
    msg_box=gr.Textbox(placeholder="Ask anything...",label="Your question")
    submit_btn=gr.Button("send",variant="Primary")

    with gr.Accordion("🔍 Agent Reasoning Trace",open=False):
        trace_box = gr.Textbox(
            label="Tools called during last response",
            lines=6, interactive=False
        )

    def handle_submit(message, history, session_id):
        return chat(message, history, session_id, "")

    submit_btn.click(
        handle_submit,
        inputs=[msg_box, chatbot, session_id],
        outputs=[chatbot, session_id, trace_box]
    ).then(lambda: "", outputs=msg_box)

    msg_box.submit(
        handle_submit,
        inputs=[msg_box, chatbot, session_id],
        outputs=[chatbot, session_id, trace_box]
    ).then(lambda: "", outputs=msg_box)

if __name__ == "__main__":
    demo.launch(share=True)
