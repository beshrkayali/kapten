from typing import Any, Dict, List, Tuple

import httpx

from . import __version__


def parse_webhook_payload(
    payload: Dict[str, Any], tracked_repositories: List[str]
) -> Tuple[str, str]:
    # Validate payload structure
    valid_structure = payload and (
        payload.get("callback_url")
        and "repository" in payload
        and payload["repository"].get("repo_name")
        and "push_data" in payload
        and payload["push_data"].get("tag")
    )
    if not valid_structure:
        raise ValueError("Invalid dockerhub payload")

    # Validate repository
    repository = payload["repository"]["repo_name"]
    if repository not in tracked_repositories:
        raise ValueError(f"Non-tracked dockerhub repository: {repository}")

    # Validate callback url
    callback_url = payload["callback_url"]
    repository_url = f"https://registry.hub.docker.com/u/{repository}/hook/"
    if not callback_url.startswith(repository_url):
        raise ValueError(f"Invalid dockerhub callback url: {callback_url}")

    tag = payload["push_data"]["tag"]
    image = f"{repository}:{tag}"
    return image, callback_url


async def callback(url: str, description: str, state: str = "success") -> bool:
    payload = {
        "state": state,
        "context": f"Kapten {__version__}",
        "description": description[:255],
    }
    response = await httpx.post(url, json=payload)
    return not response.is_error
