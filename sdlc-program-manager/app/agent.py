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

import uuid
from typing import Any, Dict, List, Optional
from google.adk.agents import Agent
from google.adk.apps import App
from google.adk.models import Gemini
from google.adk.tools import ToolContext
from google import genai
from google.cloud import firestore, storage
from google.genai import types

PROJECT_ID = "qwiklabs-gcp-04-0d49d311856f"
GCS_BUCKET_NAME = "qwiklabs-gcp-04-0d49d311856f-sdlc-artifacts"
COLLECTION_NAME = "sdlc_tasks"
MODEL = "gemini-2.5-flash"
IMAGE_MODEL = "gemini-3.1-flash-lite-image"
VIDEO_MODEL = "gemini-omni-flash-preview"


def _get_firestore_client() -> firestore.Client:
    return firestore.Client(project=PROJECT_ID)


def list_sdlc_tasks(stage: Optional[str] = None) -> List[Dict[str, Any]]:
    """List SDLC tasks from the Firestore database, optionally filtered by pipeline stage.

    Args:
        stage: Optional pipeline stage to filter by (e.g. 'Requirements', 'Coding', 'Testing', 'Deployment').

    Returns:
        A list of task dictionaries containing id, title, description, stage, sub_agent, status, priority, deliverables, and blockers.
    """
    db = _get_firestore_client()
    query = db.collection(COLLECTION_NAME)
    if stage:
        query = query.where("stage", "==", stage)

    docs = query.stream()
    tasks = []
    for doc in docs:
        task_data = doc.to_dict()
        task_data["id"] = doc.id
        tasks.append(task_data)
    return tasks


def get_sdlc_task(task_id: str) -> Dict[str, Any]:
    """Retrieve full details of a specific SDLC task by its ID.

    Args:
        task_id: The unique task identifier (e.g., 'TASK-101').

    Returns:
        The task details dictionary if found, or an error message dict.
    """
    db = _get_firestore_client()
    doc_ref = db.collection(COLLECTION_NAME).document(task_id)
    doc = doc_ref.get()
    if not doc.exists:
        return {"error": f"Task '{task_id}' not found."}
    data = doc.to_dict()
    data["id"] = doc.id
    return data


def save_sdlc_task(
    task_id: str,
    title: str,
    description: str,
    stage: str,
    sub_agent: str,
    status: str = "Pending",
    priority: str = "Medium",
    deliverables: Optional[List[str]] = None,
    blockers: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Create or update an SDLC task in Firestore.

    Args:
        task_id: Unique task identifier (e.g., 'TASK-105').
        title: Short title of the task.
        description: Detailed description of what needs to be accomplished.
        stage: Pipeline stage ('Requirements', 'Coding', 'Testing', 'Deployment').
        sub_agent: Assigned sub-agent (e.g. 'PRD Requirements Agent', 'Coding Agent', 'Testing Agent', 'Release Agent').
        status: Current task status ('Pending', 'In Progress', 'Completed', 'Blocked').
        priority: Priority level ('Low', 'Medium', 'High', 'Critical').
        deliverables: List of files, PRs, or documents produced by the task.
        blockers: List of dependencies or blockers holding back this task.

    Returns:
        A confirmation dictionary indicating success and saved task attributes.
    """
    db = _get_firestore_client()
    doc_ref = db.collection(COLLECTION_NAME).document(task_id)
    payload = {
        "id": task_id,
        "title": title,
        "description": description,
        "stage": stage,
        "sub_agent": sub_agent,
        "status": status,
        "priority": priority,
        "deliverables": deliverables or [],
        "blockers": blockers or [],
    }
    doc_ref.set(payload, merge=True)
    return {"status": "success", "message": f"Task '{task_id}' saved successfully.", "task": payload}


def update_task_status(task_id: str, status: str, blocker: Optional[str] = None) -> Dict[str, Any]:
    """Update the status of an existing SDLC task and optionally add a blocker.

    Args:
        task_id: Unique task identifier (e.g., 'TASK-102').
        status: New status ('Pending', 'In Progress', 'Completed', 'Blocked').
        blocker: Optional blocker note to record.

    Returns:
        Confirmation dictionary with the updated task status.
    """
    db = _get_firestore_client()
    doc_ref = db.collection(COLLECTION_NAME).document(task_id)
    doc = doc_ref.get()
    if not doc.exists:
        return {"error": f"Task '{task_id}' not found."}

    data = doc.to_dict()
    updates = {"status": status}
    if blocker:
        existing_blockers = data.get("blockers", [])
        if blocker not in existing_blockers:
            existing_blockers.append(blocker)
        updates["blockers"] = existing_blockers

    doc_ref.update(updates)
    return {"status": "success", "message": f"Task '{task_id}' status updated to '{status}'."}


def evaluate_release_readiness() -> Dict[str, Any]:
    """Evaluate whether the initiative is ready for release based on SDLC task statuses, blockers, and deliverables.

    Returns:
        A dictionary with ready boolean, score percentage, active blockers, pending stages, and release recommendation.
    """
    db = _get_firestore_client()
    docs = db.collection(COLLECTION_NAME).stream()

    total_tasks = 0
    completed_tasks = 0
    active_blockers: List[str] = []
    uncompleted_stages: set = set()

    for doc in docs:
        total_tasks += 1
        t = doc.to_dict()
        status = t.get("status", "Pending")
        stage = t.get("stage", "Unknown")
        blockers = t.get("blockers", [])

        if status == "Completed":
            completed_tasks += 1
        else:
            uncompleted_stages.add(stage)

        if blockers:
            for b in blockers:
                active_blockers.append(f"[{t.get('id', doc.id)} - {stage}] {b}")

    score = int((completed_tasks / total_tasks * 100)) if total_tasks > 0 else 0
    is_ready = (len(active_blockers) == 0) and (score == 100)

    if is_ready:
        recommendation = "GO FOR RELEASE: All stages completed with zero blockers."
    elif active_blockers:
        recommendation = f"NO-GO: Release blocked by {len(active_blockers)} active blocker(s)."
    else:
        recommendation = f"NO-GO: Initiative in progress ({score}% complete). Awaiting completion of: {', '.join(sorted(uncompleted_stages))}."

    return {
        "ready_for_release": is_ready,
        "completion_score": f"{score}%",
        "total_tasks": total_tasks,
        "completed_tasks": completed_tasks,
        "active_blockers": active_blockers,
        "pending_stages": sorted(list(uncompleted_stages)),
        "recommendation": recommendation,
    }


def check_github_repo_health(repo: str = "google/adk-python") -> Dict[str, Any]:
    """Fetch live repository health, release info, and open issue counts from GitHub's public API.

    Args:
        repo: Repository in 'owner/repo' format (e.g. 'google/adk-python' or 'facebook/react').

    Returns:
        A dictionary containing repo stats, latest release tag, open issues count, and default branch.
    """
    import os
    import urllib.request
    import json

    token = os.environ.get("GITHUB_TOKEN")
    headers = {"User-Agent": "SDLC-Program-Manager-Agent"}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    base_url = f"https://api.github.com/repos/{repo}"
    req = urllib.request.Request(base_url, headers=headers)

    try:
        with urllib.request.urlopen(req, timeout=5) as response:
            repo_data = json.loads(response.read().decode())
    except Exception as e:
        return {"error": f"Failed to fetch repository '{repo}': {str(e)}"}

    latest_tag = "None"
    try:
        rel_req = urllib.request.Request(f"{base_url}/releases/latest", headers=headers)
        with urllib.request.urlopen(rel_req, timeout=5) as rel_response:
            rel_data = json.loads(rel_response.read().decode())
            latest_tag = rel_data.get("tag_name", "None")
    except Exception:
        pass

    return {
        "repository": repo,
        "description": repo_data.get("description"),
        "default_branch": repo_data.get("default_branch"),
        "open_issues": repo_data.get("open_issues_count"),
        "stars": repo_data.get("stargazers_count"),
        "latest_release": latest_tag,
        "html_url": repo_data.get("html_url"),
    }


async def generate_architecture_diagram(
    prompt: str,
    tool_context: ToolContext,
    filename: Optional[str] = None,
) -> Dict[str, Any]:
    """Generate a software architecture or SDLC workflow visual using gemini-3.1-flash-lite-image in global region.

    Saves the image to the Playground's Artifacts panel via tool_context.save_artifact, uploads the image bytes
    to the public Cloud Storage bucket, and returns its public HTTPS URL.

    Args:
        prompt: Description of the architecture diagram, UI mockup, or milestone visual to generate.
        tool_context: The ADK tool execution context injected automatically.
        filename: Optional filename for the image artifact (defaults to generated UUID).

    Returns:
        A dictionary containing the public GCS URL, artifact filename, and status.
    """
    client = genai.Client(vertexai=True, project=PROJECT_ID, location="global")
    response = client.models.generate_content(
        model=IMAGE_MODEL,
        contents=f"Software architecture technical diagram, clean modern UI vector style: {prompt}",
        config=types.GenerateContentConfig(
            response_modalities=["IMAGE"],
        ),
    )

    image_bytes = None
    mime_type = "image/jpeg"
    for candidate in response.candidates:
        if candidate.content and candidate.content.parts:
            for part in candidate.content.parts:
                if part.inline_data:
                    image_bytes = part.inline_data.data
                    mime_type = part.inline_data.mime_type or "image/jpeg"
                    break
        if image_bytes:
            break

    if not image_bytes:
        return {"error": "Failed to generate image from prompt."}

    ext = "jpg" if "jpeg" in mime_type else "png"
    artifact_name = filename or f"diagram_{uuid.uuid4().hex[:8]}.{ext}"

    # (1) Save artifact so it shows up in Playground's Artifacts panel
    try:
        artifact_part = types.Part.from_bytes(data=image_bytes, mime_type=mime_type)
        await tool_context.save_artifact(filename=artifact_name, artifact=artifact_part)
    except Exception as e:
        print(f"Warning: Could not save artifact to tool_context: {e}")

    # (2) Upload image bytes directly to the public Cloud Storage bucket
    storage_client = storage.Client(project=PROJECT_ID)
    bucket = storage_client.bucket(GCS_BUCKET_NAME)
    blob = bucket.blob(artifact_name)
    blob.upload_from_string(image_bytes, content_type=mime_type)

    public_url = f"https://storage.googleapis.com/{GCS_BUCKET_NAME}/{artifact_name}"

    return {
        "status": "success",
        "public_url": public_url,
        "artifact_filename": artifact_name,
        "prompt": prompt,
    }


async def generate_sdlc_milestone_video(
    prompt: str,
    tool_context: ToolContext,
    filename: Optional[str] = None,
) -> Dict[str, Any]:
    """Generate a short animation/video for an SDLC initiative or milestone using gemini-omni-flash-preview in global region.

    Saves the video to the Playground's Artifacts panel via tool_context.save_artifact, uploads the video bytes
    to the public Cloud Storage bucket, and returns its public HTTPS URL.

    Args:
        prompt: Description of the software release animation, demo, deployment pipeline, or milestone visual.
        tool_context: The ADK tool execution context injected automatically.
        filename: Optional filename for the video artifact (defaults to generated UUID .mp4).

    Returns:
        A dictionary containing the public GCS URL, artifact filename, and status.
    """
    import base64

    client = genai.Client(vertexai=True, project=PROJECT_ID, location="global")
    interaction = client.interactions.create(
        model=VIDEO_MODEL,
        input=f"Software development lifecycle milestone animation, 3D smooth render: {prompt}",
    )

    if not hasattr(interaction, "output_video") or not interaction.output_video:
        return {"error": "Failed to generate video from prompt."}

    raw_data = interaction.output_video.data
    if isinstance(raw_data, str):
        video_bytes = base64.b64decode(raw_data)
    elif isinstance(raw_data, bytes):
        video_bytes = raw_data
    else:
        return {"error": "Unexpected video output format received from model."}

    mime_type = getattr(interaction.output_video, "mime_type", None) or "video/mp4"
    artifact_name = filename or f"milestone_video_{uuid.uuid4().hex[:8]}.mp4"

    # (1) Save artifact so it shows up in Playground's Artifacts panel
    try:
        artifact_part = types.Part.from_bytes(data=video_bytes, mime_type=mime_type)
        await tool_context.save_artifact(filename=artifact_name, artifact=artifact_part)
    except Exception as e:
        print(f"Warning: Could not save video artifact to tool_context: {e}")

    # (2) Upload video bytes directly to the public Cloud Storage bucket
    storage_client = storage.Client(project=PROJECT_ID)
    bucket = storage_client.bucket(GCS_BUCKET_NAME)
    blob = bucket.blob(artifact_name)
    blob.upload_from_string(video_bytes, content_type=mime_type)

    public_url = f"https://storage.googleapis.com/{GCS_BUCKET_NAME}/{artifact_name}"

    return {
        "status": "success",
        "public_url": public_url,
        "artifact_filename": artifact_name,
        "prompt": prompt,
    }


from google.adk.agents.callback_context import CallbackContext
from google.adk.tools.preload_memory_tool import PreloadMemoryTool
from a2ui.schema.manager import A2uiSchemaManager
from a2ui.basic_catalog.provider import BasicCatalog
from .a2ui_utils import a2ui_callback

MEMORY_BANK_ID = "1177086571162107904"
MEMORY_BANK_LOCATION = "us-east1"


async def generate_memories_callback(callback_context: CallbackContext):
    """WRITE: after each turn, send the session events to Memory Bank for extraction."""
    await callback_context.add_session_to_memory()
    return None


schema_manager = A2uiSchemaManager(
    version="0.8",
    catalogs=[BasicCatalog.get_config("0.8")],
)

role_description = (
    "You are the Virtual SDLC Program Manager Orchestrator leading automated software delivery. "
    "You oversee and coordinate specialized sub-agents across the entire lifecycle: "
    "PRD Requirements Agent, Coding Agent, Testing Agent, and Release Agent.\n\n"
    "MEMORY & RELEASE RECORDING:\n"
    "- Whenever you evaluate release readiness or encounter an initiative, sprint, or release that is NOT ready "
    "(status 'NO-GO', blocked, or incomplete), explicitly state and summarize the release details, the unresolved blockers, "
    "and the pending stages in your response as a durable release incident record so it is captured into long-term memory.\n"
    "- You continuously recall and track across sessions all past releases that were not ready, why they were blocked, "
    "and which gates failed, warning the user of recurring bottlenecks or unresolved blockers from earlier attempts.\n\n"
    "SDLC ORCHESTRATION & TOOLS:\n"
    "You maintain and query the project state via Firestore tools (list_sdlc_tasks, get_sdlc_task, "
    "save_sdlc_task, update_task_status, evaluate_release_readiness) to track deliverables, "
    "stages, blockers, and evaluate release gates. You monitor external codebase health via "
    "check_github_repo_health, generate architecture diagrams or visual mockups via "
    "generate_architecture_diagram, and generate short SDLC milestone animations/videos via "
    "generate_sdlc_milestone_video."
)

instruction = schema_manager.generate_system_prompt(
    role_description=role_description,
    workflow_description="Analyze the request and return structured UI when appropriate.",
    ui_description=(
        "Keep every surface tiny and flat: ONE Card > ONE Column > a few Text rows. "
        "Never nest a Card inside a Card. "
        "Use ONLY these components: Card, Column, Row, Text, and Image. Do not use "
        "Table or Heading (unsupported), or Buttons, actions, or forms (they do "
        "nothing in adk web). "
        "You may include one Image component, but only when you have a public https "
        "URL for the image (for example the URL an image tool returns after uploading "
        "to a public bucket). Set the Image url to that exact https link, for example "
        "{\"Image\": {\"url\": {\"literalString\": \"https://...\"}}}. Never point an "
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
        model=MODEL,
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    instruction=instruction,
    tools=[
        PreloadMemoryTool(),
        list_sdlc_tasks,
        get_sdlc_task,
        save_sdlc_task,
        update_task_status,
        evaluate_release_readiness,
        check_github_repo_health,
        generate_architecture_diagram,
        generate_sdlc_milestone_video,
    ],
    after_model_callback=a2ui_callback,
    after_agent_callback=generate_memories_callback,
)

app = App(
    root_agent=root_agent,
    name="app",
)
