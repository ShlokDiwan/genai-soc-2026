import uuid
import gradio as gr
from agent import agent
from tools_rag import index_documents
from tools_vision import img_to_data, describe_image
def handle_pdf_upload(file):
    if file is None:
        return "No file uploaded."
    n_chunks = index_documents([file.name])
    return f"Indexed {n_chunks} chunks into ChromaDB."

def chat(message, image, history, session_id):
    trace_log, final_answer = [], ""
    display_message = message
    if image is not None:
        data_uri = img_to_data(image)

        image_description = describe_image.invoke(
            {"image_data": data_uri}
      )
        print("=" * 60)
        print(image_description)
        print("=" * 60)
        trace_log.append("→ describe_image")
        agent_message = f"""
                        User uploaded an image.
                        Image description:
                        {image_description}
                        User question:
                        {message}
                        """
    else:
        agent_message = message

    config = {
        "configurable": {"thread_id": session_id},
    }
    
    try:
        
        for event in agent.stream(
            {"messages": [{"role": "user", "content": agent_message}]},
            config=config, stream_mode="values",
        ):
            last = event["messages"][-1]
            if getattr(last, "tool_calls", None):
                for tc in last.tool_calls:
                    trace_log.append(f"→ {tc['name']}: {tc['args']}")
            elif last.type == "ai" and not last.tool_calls:
                final_answer = last.content

        history.append(
            {"role": "user", "content": display_message}
        )

        history.append(
            {"role": "assistant", "content": final_answer}
        )

        return history, session_id, "\n".join(trace_log) or "No tools were called."
    except Exception as e:
        print(f"chat() error: {e}")

        history.append(
            {"role": "user", "content": message}
        )

        history.append(
            {"role": "assistant", "content": f"⚠️ Error: {e}"}
        )
        return history, session_id, "\n".join(trace_log) or "No tools were called."


with gr.Blocks(title="HybridSight") as demo:
    session_id = gr.State(value=lambda: str(uuid.uuid4()))
    gr.Markdown("# 👁️ HybridSight — RAG + Web + Vision Agent")

    with gr.Row():
        pdf_upload = gr.File(label="Upload a PDF", file_types=[".pdf"])
        image_upload = gr.Image(label="Upload an image", type="filepath")
    index_status = gr.Textbox(label="Indexing status", interactive=False)
    pdf_upload.change(handle_pdf_upload, inputs=pdf_upload, outputs=index_status)

    chatbot = gr.Chatbot(height=420, label="Conversation")
    msg_box = gr.Textbox(placeholder="Ask anything...", label="Your message")
    submit_btn = gr.Button("Send", variant="primary")

    with gr.Accordion("🔍 Agent Reasoning Trace", open=False):
        trace_box = gr.Textbox(label="Tools called during last response", lines=6, interactive=False)

    submit_btn.click(
        chat, inputs=[msg_box, image_upload, chatbot, session_id],
        outputs=[chatbot, session_id, trace_box],
    ).then(lambda: "", outputs=msg_box)
    msg_box.submit(
    chat,
    inputs=[msg_box, image_upload, chatbot, session_id],
    outputs=[chatbot, session_id, trace_box],
).then(
    lambda: "",
    outputs=msg_box,
)
if __name__ == "__main__":
    demo.launch(debug=True)