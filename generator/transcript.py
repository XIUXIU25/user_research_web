#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Generate interview transcripts:
- Reads all users from mongo-user (27017), db=user, col=users
- Reads all projects from mongo-project (27018), db=project, col=projects
- For each (user, project), calls Ollama gpt-oss:20b to produce:
    { "transcript": str, "estimated_interview_duration_minutes": int }
- Stores into mongo-interview-history (27019), db=interview_history, col=transcripts:
    { userId, projectId, transcript, interviewingTime, createdAt }
"""

import os
import json
import time
from datetime import datetime, timezone
from typing import Dict, Any, List, Tuple
import random

import requests
from pymongo import MongoClient, ASCENDING
from bson import ObjectId

# -----------------------------
# Config (env overrides allowed)
# -----------------------------
USER_MONGO_URI = os.getenv("USER_MONGO_URI", "mongodb://root:example@localhost:27017/")
PROJECT_MONGO_URI = os.getenv("PROJECT_MONGO_URI", "mongodb://root:example@localhost:27018/")
HISTORY_MONGO_URI = os.getenv("HISTORY_MONGO_URI", "mongodb://root:example@localhost:27019/")

USER_DB_NAME = os.getenv("USER_DB_NAME", "user")
USER_COLLECTION = os.getenv("USER_COLLECTION", "users")

PROJECT_DB_NAME = os.getenv("PROJECT_DB_NAME", "project")
PROJECT_COLLECTION = os.getenv("PROJECT_COLLECTION", "projects")

HISTORY_DB_NAME = os.getenv("HISTORY_DB_NAME", "interview_history")
HISTORY_COLLECTION = os.getenv("HISTORY_COLLECTION", "interview_histories")

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "gpt-oss:20b")
TEMPERATURE = float(os.getenv("OLLAMA_TEMPERATURE", "0.7"))

# -----------------------------
# Mongo clients & collections
# -----------------------------
user_client = MongoClient(USER_MONGO_URI)
project_client = MongoClient(PROJECT_MONGO_URI)
history_client = MongoClient(HISTORY_MONGO_URI)

users_col = user_client[USER_DB_NAME][USER_COLLECTION]
projects_col = project_client[PROJECT_DB_NAME][PROJECT_COLLECTION]
history_col = history_client[HISTORY_DB_NAME][HISTORY_COLLECTION]

# Optional: avoid exact duplicates (same day) by indexing; adjust if you want hard uniqueness
history_col.create_index(
    [("userId", ASCENDING), ("projectId", ASCENDING), ("createdAt", ASCENDING)]
)

# -----------------------------
# Helpers
# -----------------------------
def fmt_money(x):
    try:
        return round(float(x), 2)
    except Exception:
        return x

def normalize_user(u: Dict[str, Any]) -> Dict[str, Any]:
    """Match your example user schema exactly."""
    return {
        "_id": u.get("_id"),  # ObjectId
        "first_name": u.get("first_name"),
        "last_name": u.get("last_name"),
        "age": u.get("age"),
        "sex": u.get("sex"),
        "occupation": u.get("occupation"),
        "location": u.get("location"),
        "monthly_income": u.get("monthly_income"),
    }

def normalize_project(p: Dict[str, Any]) -> Dict[str, Any]:
    """Match your example project schema exactly."""
    guide = p.get("interviewGuide") or []
    if isinstance(guide, str):
        guide = [guide]
    guide = [str(q) for q in guide]

    return {
        "_id": p.get("_id"),  # ObjectId
        "name": p.get("name"),
        "interviewGuide": guide,
        "estimatedInterviewDuration": p.get("estimatedInterviewDuration"),
        "createdAt": p.get("createdAt"),
        "updatedAt": p.get("updatedAt"),
    }

def build_prompt(user: Dict[str, Any], project: Dict[str, Any]) -> str:
    """
    Ask Ollama to return strict JSON:
      { "transcript": str, "estimated_interview_duration_minutes": int }
    """
    guide_lines = "\n".join([f"- {q}" for q in project["interviewGuide"]]) or "- Ask about experience, needs, budget, and decision factors."
    duration_hint = project.get("estimatedInterviewDuration")

    return f"""You are an expert qualitative interviewer. Generate a realistic **dialog** between an Interviewer and a Participant.

OUTPUT (STRICT):
Return ONLY a valid JSON object with EXACTLY:
  "transcript": string,  // multi-line; each line begins with "Interviewer:" or "Participant:"
  "estimated_interview_duration_minutes": integer

NO markdown, NO commentary, NO backticks — JSON ONLY.

PARTICIPANT
- Name: {user.get("first_name","")} {user.get("last_name","")}
- Age: {user.get("age")}
- Sex: {user.get("sex")}
- Occupation: {user.get("occupation")}
- Location: {user.get("location")}
- Monthly Income (USD): {fmt_money(user.get("monthly_income"))}

PROJECT
- Name: {project.get("name")}
- Interview Guide (themes; ask natural follow-ups):
{guide_lines}
- Target duration hint (minutes): {duration_hint if duration_hint is not None else "none"}

REQUIREMENTS
- 12–20 total lines (each line = one speaker turn).
- Keep it natural, and consistent with the participant.
- Estimate a realistic duration in minutes based on depth & follow-ups.
- IMPORTANT: Respond with JSON only.
"""

def call_ollama(prompt: str) -> Tuple[str, int]:
    """Calls Ollama /api/generate (non-streaming) and parses the strict-JSON response."""
    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": TEMPERATURE},
    }
    resp = requests.post(f"{OLLAMA_URL}/api/generate", json=payload, timeout=1800)
    resp.raise_for_status()
    text = resp.json().get("response", "")
    data = json.loads(text)  # model instructed to return JSON only
    return data["transcript"], int(data["estimated_interview_duration_minutes"])

def save_history(user_oid: ObjectId, project_oid: ObjectId, transcript: str, minutes: int) -> None:
    doc = {
        "userId": user_oid,            # ObjectId of user._id
        "projectId": project_oid,      # ObjectId of project._id
        "transcript": transcript,
        "interviewingTime": minutes,   # minutes
        "createdAt": datetime.now(timezone.utc),
    }
    history_col.insert_one(doc)

# -----------------------------
# Main
# -----------------------------
def main():
    users_raw = list(users_col.find({}))
    projects_raw = list(projects_col.find({}))

    if not users_raw:
        print("No users found in mongo-user.")
        return
    if not projects_raw:
        print("No projects found in mongo-project.")
        return

    users = [normalize_user(u) for u in users_raw]
    projects = [normalize_project(p) for p in projects_raw]

    print(f"Found {len(users)} users and {len(projects)} projects. Generating transcripts for all pairs...")

    total = 0
    for u in users:
        # pick a single random project
        p = random.choice(projects)

        prompt = build_prompt(u, p)
        transcript, minutes = call_ollama(prompt)
        save_history(u["_id"], p["_id"], transcript, minutes)

        total += 1
        # light pacing so we don't crush a local CPU/GPU
        time.sleep(0.05)
        print(f"Saved transcript: user={u['_id']} project={p['_id']} ({minutes} min)")

    print(f"Done. Generated {total} interview transcripts.")

if __name__ == "__main__":
    main()