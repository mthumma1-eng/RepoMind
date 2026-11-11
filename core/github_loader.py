import hashlib
import re
from urllib.parse import urlparse
import git
from git.exc import GitCommandError, InvalidGitRepositoryError
from core.config import DATA_DIR

def validate_github_url(url: str):
    parsed = urlparse(url.strip())
    if parsed.scheme != "https" or parsed.hostname != "github.com":
        raise ValueError("Use a public HTTPS GitHub URL, e.g. https://github.com/owner/repository")
    if parsed.query or parsed.fragment or parsed.port:
        raise ValueError("Remove query parameters, fragments, or custom ports from the URL.")
    parts = parsed.path.strip("/").removesuffix(".git").split("/")
    if len(parts) != 2 or not all(re.fullmatch(r"[A-Za-z0-9_.-]+", p or "") for p in parts):
        raise ValueError("URL must have this format: https://github.com/owner/repository")
    if any(p in {".", ".."} for p in parts):
        raise ValueError("Invalid repository path.")
    return parts[0], parts[1]

def clone_repository(url: str):
    owner, name = validate_github_url(url)
    key = hashlib.sha256(url.strip().encode()).hexdigest()[:12]
    destination = DATA_DIR / f"{owner}_{name}_{key}"
    if destination.exists():
        try:
            git.Repo(destination)
            return {"owner": owner, "name": name, "path": str(destination), "status": "cached"}
        except InvalidGitRepositoryError:
            raise RuntimeError("A non-Git folder already exists at the repository destination.")
    try:
        git.Repo.clone_from(url.strip(), destination, depth=1, multi_options=["--no-tags"])
    except GitCommandError as exc:
        raise RuntimeError("Clone failed. Confirm the repository is public and the URL is correct.") from exc
    return {"owner": owner, "name": name, "path": str(destination), "status": "cloned"}
