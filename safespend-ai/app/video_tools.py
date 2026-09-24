"""Video generation tool for SafeSpend AI using gemini-omni-flash-preview and Cloud Storage."""

import uuid
from google import genai
from google.adk.tools import ToolContext
from google.cloud import storage
from google.genai import types

# HARDCODED Project ID and Bucket Name
PROJECT_ID = "qwiklabs-gcp-01-fa8e86a4b8f6"
BUCKET_NAME = "safespend-ai-assets-qwiklabs-gcp-01-fa8e86a4b8f6"


def generate_item_video(item_name: str, tool_context: ToolContext) -> dict:
    """Generates a short video for a requested expense item in the agent's domain using
    Google's Omni model (gemini-omni-flash-preview) in the global region, saves it as
    a session artifact, and uploads it to public Cloud Storage.

    Args:
        item_name: The name or description of the requested expense item (e.g. 'Espresso Machine', 'Laptop', 'Mountain Bike').
        tool_context: The ADK tool context providing artifact storage capabilities.

    Returns:
        A dictionary containing status, item_name, public_url, and artifact_filename.
    """
    client = genai.Client(
        vertexai=True,
        project=PROJECT_ID,
        location="global",
    )

    prompt = f"A short video preview showcasing the {item_name} product in a modern, clean setting."
    response = client.models.generate_content(
        model="gemini-omni-flash-preview",
        contents=prompt,
        config=types.GenerateContentConfig(
            response_modalities=["VIDEO"],
        ),
    )

    if not response.candidates or not response.candidates[0].content.parts:
        return {"status": "error", "message": f"Failed to generate video for '{item_name}'."}

    part = response.candidates[0].content.parts[0]
    if not part.inline_data or not part.inline_data.data:
        return {"status": "error", "message": "No video data returned from model."}

    video_bytes = part.inline_data.data
    mime_type = part.inline_data.mime_type or "video/mp4"
    ext = "mp4"

    unique_id = uuid.uuid4().hex[:8]
    filename = f"{item_name.lower().replace(' ', '_')}_{unique_id}.{ext}"

    # (1) Save video bytes with tool_context.save_artifact for Playground Artifacts panel
    artifact_part = types.Part.from_bytes(data=video_bytes, mime_type=mime_type)
    tool_context.save_artifact(filename=filename, artifact=artifact_part)

    # (2) Upload video bytes directly to public Cloud Storage bucket
    storage_client = storage.Client(project=PROJECT_ID)
    bucket = storage_client.bucket(BUCKET_NAME)
    blob = bucket.blob(filename)
    blob.upload_from_string(video_bytes, content_type=mime_type)

    public_url = f"https://storage.googleapis.com/{BUCKET_NAME}/{filename}"

    return {
        "status": "success",
        "item_name": item_name,
        "artifact_filename": filename,
        "public_url": public_url,
    }
