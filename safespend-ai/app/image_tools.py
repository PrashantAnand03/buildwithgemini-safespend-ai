"""Image generation tool for SafeSpend AI using gemini-3.1-flash-lite-image and Cloud Storage."""

import uuid
from google import genai
from google.adk.tools import ToolContext
from google.cloud import storage
from google.genai import types

# HARDCODED Project ID and Bucket Name
PROJECT_ID = "qwiklabs-gcp-01-fa8e86a4b8f6"
BUCKET_NAME = "safespend-ai-assets-qwiklabs-gcp-01-fa8e86a4b8f6"


def generate_item_image(item_name: str, tool_context: ToolContext) -> dict:
    """Generates a visual image for a requested expense item using AI multimodal generation,
    saves it as a session artifact, and uploads it to public Cloud Storage.

    Args:
        item_name: The name or description of the requested expense item (e.g. 'Laptop', 'Smartwatch', 'Mountain Bike').
        tool_context: The ADK tool context providing artifact storage capabilities.

    Returns:
        A dictionary containing status, item_name, public_url, and artifact_name.
    """
    client = genai.Client(
        vertexai=True,
        project=PROJECT_ID,
        location="global",
    )

    prompt = f"A realistic high quality product photo of {item_name} on a clean minimal background."
    response = client.models.generate_content(
        model="gemini-3.1-flash-lite-image",
        contents=prompt,
        config=types.GenerateContentConfig(
            response_modalities=["IMAGE"],
        ),
    )

    if not response.candidates or not response.candidates[0].content.parts:
        return {"status": "error", "message": f"Failed to generate image for '{item_name}'."}

    part = response.candidates[0].content.parts[0]
    if not part.inline_data or not part.inline_data.data:
        return {"status": "error", "message": "No image data returned from model."}

    image_bytes = part.inline_data.data
    mime_type = part.inline_data.mime_type or "image/jpeg"
    ext = "png" if "png" in mime_type else "jpg"

    unique_id = uuid.uuid4().hex[:8]
    filename = f"{item_name.lower().replace(' ', '_')}_{unique_id}.{ext}"

    # (1) Save image bytes with tool_context.save_artifact for Playground Artifacts panel
    artifact_part = types.Part.from_bytes(data=image_bytes, mime_type=mime_type)
    tool_context.save_artifact(filename=filename, artifact=artifact_part)

    # (2) Upload image bytes directly to public Cloud Storage bucket
    storage_client = storage.Client(project=PROJECT_ID)
    bucket = storage_client.bucket(BUCKET_NAME)
    blob = bucket.blob(filename)
    blob.upload_from_string(image_bytes, content_type=mime_type)

    public_url = f"https://storage.googleapis.com/{BUCKET_NAME}/{filename}"

    return {
        "status": "success",
        "item_name": item_name,
        "artifact_filename": filename,
        "public_url": public_url,
    }
