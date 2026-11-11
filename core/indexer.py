import ast
import hashlib
from pathlib import Path
from core.config import (
    IGNORED_DIRS, SUPPORTED_EXTENSIONS, LANGUAGES, MAX_FILES,
    MAX_FILE_BYTES, MAX_TOTAL_BYTES, CHUNK_LINES, CHUNK_OVERLAP
)

def _python_chunks(text, rel_path):
    lines = text.splitlines()
    chunks = []
    try:
        tree = ast.parse(text)
        nodes = [n for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))]
        covered = set()
        for node in sorted(nodes, key=lambda n: getattr(n, "lineno", 0)):
            start = max(1, getattr(node, "lineno", 1))
            end = min(len(lines), getattr(node, "end_lineno", start))
            content = "\n".join(lines[start-1:end])
            name = getattr(node, "name", "unknown")
            kind = "class" if isinstance(node, ast.ClassDef) else "function"
            chunks.append({"path": rel_path, "content": content, "start_line": start,
                           "end_line": end, "language": "python", "symbol": f"{kind} {name}"})
            covered.update(range(start, end + 1))
    except SyntaxError:
        pass
    # Preserve module-level code and ensure non-Python files are chunked too.
    if not chunks:
        for start in range(1, len(lines) + 1, CHUNK_LINES - CHUNK_OVERLAP):
            end = min(len(lines), start + CHUNK_LINES - 1)
            content = "\n".join(lines[start-1:end])
            if content.strip():
                chunks.append({"path": rel_path, "content": content, "start_line": start,
                               "end_line": end, "language": "python", "symbol": "module"})
    return chunks

def _line_chunks(text, rel_path, language):
    lines = text.splitlines()
    result = []
    step = CHUNK_LINES - CHUNK_OVERLAP
    for start in range(1, len(lines) + 1, step):
        end = min(len(lines), start + CHUNK_LINES - 1)
        content = "\n".join(lines[start-1:end])
        if content.strip():
            result.append({"path": rel_path, "content": content, "start_line": start,
                           "end_line": end, "language": language, "symbol": "code chunk"})
    return result

def build_index(repo_path):
    root = Path(repo_path)
    chunks, files, languages = [], [], {}
    total_bytes = 0
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        rel = path.relative_to(root)
        if any(part in IGNORED_DIRS or part.startswith(".") for part in rel.parts[:-1]):
            continue
        if path.name.startswith(".") or path.suffix.lower() not in SUPPORTED_EXTENSIONS:
            continue
        try:
            size = path.stat().st_size
            if size == 0 or size > MAX_FILE_BYTES or total_bytes + size > MAX_TOTAL_BYTES:
                continue
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        language = LANGUAGES.get(path.suffix.lower(), "text")
        files.append({"path": str(rel), "language": language, "size_kb": round(size / 1024, 2)})
        languages[language] = languages.get(language, 0) + 1
        total_bytes += size
        if path.suffix.lower() == ".py":
            new_chunks = _python_chunks(text, str(rel))
        else:
            new_chunks = _line_chunks(text, str(rel), language)
        for chunk in new_chunks:
            chunk["id"] = hashlib.sha1(
                f"{rel}:{chunk['start_line']}:{chunk['content']}".encode()
            ).hexdigest()
            chunks.append(chunk)
        if len(files) >= MAX_FILES:
            break

    if not chunks:
        raise RuntimeError("No supported, non-empty source or documentation files were found.")

    return {
        "chunks": chunks, "chunk_count": len(chunks), "file_count": len(files),
        "files": files, "languages": languages, "repo_path": str(root)
    }
