from __future__ import annotations

import base64
import json
import os
from typing import List, Dict, Any

from google.oauth2 import service_account
from google.auth.transport.requests import Request
import requests


def _load_sa_credentials(path: str):
    scopes = ["https://www.googleapis.com/auth/cloud-platform"]
    creds = service_account.Credentials.from_service_account_file(path, scopes=scopes)
    creds.refresh(Request())
    return creds


def _vertex_endpoint(model: str, project: str, location: str) -> str:
    # e.g. https://us-central1-aiplatform.googleapis.com/v1/projects/PROJECT/locations/LOCATION/publishers/google/models/MODEL:generateContent
    return f"https://{location}-aiplatform.googleapis.com/v1/projects/{project}/locations/{location}/publishers/google/models/{model}:generateContent"


def vertex_generate_text(sa_path: str, project: str, location: str, model: str, prompt: str, content: str, timeout: int = 90) -> str:
    creds = _load_sa_credentials(sa_path)
    url = _vertex_endpoint(model, project, location)
    headers = {"Authorization": f"Bearer {creds.token}", "Content-Type": "application/json"}
    payload = {
        "contents": [
            {
                "role": "user",
                "parts": [
                    {"text": prompt},
                    {"text": content},
                ],
            }
        ]
    }
    r = requests.post(url, headers=headers, json=payload, timeout=timeout)
    r.raise_for_status()
    out = r.json()
    try:
        return out["candidates"][0]["content"]["parts"][0]["text"]
    except Exception:
        return json.dumps(out)


def vertex_generate_vision(sa_path: str, project: str, location: str, model: str, prompt: str, images_png: List[bytes], timeout: int = 90) -> str:
    creds = _load_sa_credentials(sa_path)
    url = _vertex_endpoint(model, project, location)
    headers = {"Authorization": f"Bearer {creds.token}", "Content-Type": "application/json"}
    parts: List[Dict[str, Any]] = [{"text": prompt}]
    for data in images_png:
        parts.append({"inlineData": {"mimeType": "image/png", "data": base64.b64encode(data).decode("utf-8")}})
    payload = {"contents": [{"role": "user", "parts": parts}]}
    r = requests.post(url, headers=headers, json=payload, timeout=timeout)
    r.raise_for_status()
    out = r.json()
    try:
        return out["candidates"][0]["content"]["parts"][0]["text"]
    except Exception:
        return json.dumps(out)

