from langchain_core.tools import tool
import os
from groq import Groq
import base64
from PIL import Image
import io
from dotenv import load_dotenv

load_dotenv()

client=Groq(api_key=os.getenv("GROQ_API_KEY"))


def img_to_data(filepath: str) -> str:
    img = Image.open(filepath)

    img.thumbnail((512, 512))

    buffer = io.BytesIO()
    img.save(buffer, format="JPEG", quality=80)

    encoded = base64.b64encode(buffer.getvalue()).decode("utf-8")

    return f"data:image/jpeg;base64,{encoded}"


@tool
def describe_image(image_data: str) -> str:
    """Describe the content of an image. Use when the user uploads an
    image or asks what's in a picture. Input must be a base64 data URI
    (e.g. 'data:image/jpeg;base64,...')."""
    try:
        response = client.chat.completions.create(
            model="meta-llama/llama-4-scout-17b-16e-instruct",
            messages=[{
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "Describe the uploaded image in detail. Mention important objects, people, text, colors, and any relevant visual information."
                },
                    {"type": "image_url", "image_url": {"url": image_data}},
                ],
            }],
        )
        return response.choices[0].message.content
    
    except Exception as e:
        return f"Could not process the image: {e}"


