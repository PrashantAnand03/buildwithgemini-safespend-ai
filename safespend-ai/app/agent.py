# ruff: noqa
# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import datetime
import json
from pathlib import Path
from zoneinfo import ZoneInfo

from a2ui.basic_catalog.provider import BasicCatalog
from a2ui.schema.manager import A2uiSchemaManager
from google.adk.agents import Agent
from google.adk.agents.callback_context import CallbackContext
from google.adk.apps import App
from google.adk.code_executors.agent_engine_sandbox_code_executor import (
    AgentEngineSandboxCodeExecutor,
)
from google.adk.memory import VertexAiMemoryBankService
from google.adk.models import Gemini
from google.adk.tools.preload_memory_tool import PreloadMemoryTool
from google.genai import types

from .a2ui_utils import a2ui_callback
from .firestore_tools import (
    get_currency_exchange_rates,
    get_financial_profile,
    get_purchase_history,
    get_recurring_obligations,
    save_purchase_evaluation,
    simulate_cashflow_projection,
)
from .image_tools import generate_item_image
from .maps_tools import find_nearby_places, geocode_address
from .video_tools import generate_item_video

# Constants
PROJECT_ID = "qwiklabs-gcp-01-fa8e86a4b8f6"
LOCATION = "us-east1"

# Load Agent Engine resource name from deployment_metadata.json
_metadata_file = Path(__file__).parent.parent / "deployment_metadata.json"
_agent_engine_id = None
if _metadata_file.exists():
    try:
        with open(_metadata_file) as f:
            _data = json.load(f)
            _agent_engine_id = _data.get("remote_agent_runtime_id")
    except Exception:
        pass

_memory_bank_id = (
    _agent_engine_id.split("/")[-1] if _agent_engine_id else "854973644688850944"
)

code_executor = (
    AgentEngineSandboxCodeExecutor(agent_engine_resource_name=_agent_engine_id)
    if _agent_engine_id
    else None
)


def memory_bank_service_builder():
    """Builds Memory Bank service for deployment on Agent Engine."""
    return VertexAiMemoryBankService(
        project=PROJECT_ID,
        location=LOCATION,
        agent_engine_id=_memory_bank_id,
    )


async def generate_memories_callback(callback_context: CallbackContext):
    """Callback triggered after each turn to store durable session facts into Memory Bank."""
    try:
        await callback_context.add_session_to_memory()
    except (ValueError, RuntimeError):
        pass
    return None


def get_weather(query: str) -> str:
    """Simulates a web search. Use it get information on weather.

    Args:
        query: A string containing the location to get weather information for.

    Returns:
        A string with the simulated weather information for the queried location.
    """
    if "sf" in query.lower() or "san francisco" in query.lower():
        return "It's 60 degrees and foggy."
    return "It's 90 degrees and sunny."


def get_current_time(query: str) -> str:
    """Simulates getting the current time for a city.

    Args:
        city: The name of the city to get the current time for.

    Returns:
        A string with the current time information.
    """
    if "sf" in query.lower() or "san francisco" in query.lower():
        tz_identifier = "America/Los_Angeles"
    else:
        return f"Sorry, I don't have timezone information for query: {query}."

    tz = ZoneInfo(tz_identifier)
    now = datetime.datetime.now(tz)
    return f"The current time for query {query} is {now.strftime('%Y-%m-%d %H:%M:%S %Z%z')}"


# Build A2UI system prompt using A2uiSchemaManager version 0.8 and BasicCatalog
schema_manager = A2uiSchemaManager(
    version="0.8",
    catalogs=[BasicCatalog.get_config("0.8")],
)

instruction = schema_manager.generate_system_prompt(
    role_description=(
        "You are SafeSpend AI, a smart financial affordability concierge. "
        "Help users evaluate whether they can safely afford an expense by analyzing their financial profile, "
        "recurring obligations, pending payments, cashflow projections, currency conversion rates, and safety buffers. "
        "You can also use Google Maps geocoding and Places tools, generate item product images, "
        "execute Python code in a secure Agent Engine sandbox, and remember key user financial facts/preferences and user health/food allergies across sessions."
    ),
    workflow_description="Analyze the request, call tools when necessary, and return structured UI when appropriate.",
    ui_description=(
        "Keep every surface tiny and flat: ONE Card > ONE Column > a few Text rows. "
        "Never nest a Card inside a Card. "
        "Use ONLY these components: Card, Column, Row, Text, and Image. Do not use "
        "Table or Heading (unsupported), or Buttons, actions, or forms (they do "
        "nothing in adk web). "
        "You may include one Image component, but only when you have a public https "
        "URL for the image (for example the URL an image tool returns after uploading "
        "to a public bucket). Set the Image url to that exact https link, for example "
        '{"Image": {"url": {"literalString": "https://..."}}}. Never point an '
        "Image at a bare filename, an artifact name, or a non-http(s) path. If you do "
        "not have a public URL, add a short Text line noting the image instead. "
        "No markdown in text; use the usageHint property ('h1', 'h2', 'body') for "
        "headings and emphasis. "
        "Output ONLY the raw A2UI JSON array — no prose, and never wrap it in "
        "<a2a_datapart_json> tags or 'kind'/'data'/'metadata' objects."
    ),
    include_schema=True,
    include_examples=True,
)

root_agent = Agent(
    name="root_agent",
    model=Gemini(
        model="gemini-flash-latest",
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    instruction=instruction,
    code_executor=code_executor,
    tools=[
        PreloadMemoryTool(),
        get_weather,
        get_current_time,
        get_financial_profile,
        get_recurring_obligations,
        get_purchase_history,
        save_purchase_evaluation,
        simulate_cashflow_projection,
        get_currency_exchange_rates,
        geocode_address,
        find_nearby_places,
        generate_item_image,
        generate_item_video,
    ],
    after_agent_callback=generate_memories_callback,
    after_model_callback=a2ui_callback,
)

app = App(
    root_agent=root_agent,
    name="app",
)
