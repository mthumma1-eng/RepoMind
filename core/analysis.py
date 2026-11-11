import ast
import re
from pathlib import Path
from core.config import IGNORED_DIRS, MAX_FILES

def scan_bugs(repo_path):
    root = Path(repo_path)
    findings = []
    checks = [
        (re.compile(r"\beval\s*\("), "Use of eval()", "HIGH",
         "eval() executes dynamically supplied expressions and can be dangerous with untrusted input.",
         "Avoid eval(); use a safe parser or explicit mapping."),
        (re.compile(r"\bexec\s*\("), "Use of exec()", "HIGH",
         "exec() executes dynamically supplied Python code.",
         "Avoid exec() unless the input is fully trusted and strictly controlled."),
        (re.compile(r"\bexcept\s*:\s*$"), "Bare except clause", "MEDIUM",
         "A bare except catches nearly every exception and can hide unexpected failures.",
         "Catch specific exception types and handle them explicitly."),
        (re.compile(r"\bpassword\s*=\s*['\"][^'\"]+['\"]", re.I), "Possible hardcoded password", "HIGH",
         "A password-like literal appears to be assigned directly in source code.",
         "Move secrets to environment variables or a secret manager."),
        (re.compile(r"\bdebug\s*=\s*True\b", re.I), "Debug mode enabled", "MEDIUM",
         "Debug mode appears to be enabled in source code.",
         "Ensure debug mode is disabled in production."),
        (re.compile(r"\bpickle\.loads?\s*\("), "Pickle deserialization", "HIGH",
         "Unpickling untrusted data can execute arbitrary code.",
         "Only unpickle trusted data; consider safer serialization formats.")
    ]
    scanned = 0
    for path in root.rglob("*.py"):
        if any(part in IGNORED_DIRS for part in path.parts):
            continue
        try:
            lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
        except OSError:
            continue
        scanned += 1
        if scanned > MAX_FILES:
            break
        for number, line in enumerate(lines, start=1):
            for pattern, title, severity, description, recommendation in checks:
                if pattern.search(line):
                    findings.append({
                        "title": title, "severity": severity,
                        "description": description, "recommendation": recommendation,
                        "path": str(path.relative_to(root)), "line": number,
                        "snippet": line.strip(), "language": "python"
                    })
    return findings

def build_architecture(repo_path):
    root = Path(repo_path)
    edges = []
    modules = set()
    for path in root.rglob("*.py"):
        if any(part in IGNORED_DIRS for part in path.parts):
            continue
        rel = path.relative_to(root)
        module = str(rel.with_suffix("")).replace("/", ".").replace("\\", ".")
        modules.add(module)
        try:
            tree = ast.parse(path.read_text(encoding="utf-8", errors="ignore"))
        except (SyntaxError, OSError):
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    edges.append({"From module": module, "Imports": alias.name})
            elif isinstance(node, ast.ImportFrom) and node.module:
                edges.append({"From module": module, "Imports": node.module})
    # Build a compact DOT graph from imports that look internal to this repo.
    known_roots = {m.split(".")[0] for m in modules}
    internal = []
    for edge in edges:
        target = edge["Imports"]
        if target.split(".")[0] in known_roots:
            internal.append(edge)
    nodes = sorted({e["From module"] for e in internal} | {e["Imports"] for e in internal})
    if not nodes:
        nodes = sorted(modules)[:18]
    dot = "digraph G { rankdir=LR; node [shape=box, style=rounded, fontname=Arial]; "
    dot += " ".join('"' + n.replace('"', '') + '";' for n in nodes[:35])
    for e in internal[:60]:
        dot += '"' + e["From module"].replace('"', '') + '" -> "' + e["Imports"].replace('"', '') + '";'
    dot += "}"
    summary = f"Detected {len(modules)} Python modules and {len(internal)} likely internal import relationships. This is a static import-level view, not a complete runtime architecture."
    return {"summary": summary, "edges": internal[:200], "dot": dot if nodes else ""}

def make_overview(repo_path, index_info):
    root = Path(repo_path)
    readme = ""
    for candidate in ("README.md", "readme.md", "README.rst"):
        p = root / candidate
        if p.exists():
            readme = p.read_text(encoding="utf-8", errors="ignore")[:5000]
            break
    langs = index_info["languages"]
    lang_text = "\n".join(f"- {k}: {v} files" for k, v in sorted(langs.items()))
    report = f"""# Repository onboarding report

## Repository overview
- Repository: `{root.name}`
- Files indexed: {index_info['file_count']}
- Code/document chunks: {index_info['chunk_count']}

## Languages
{lang_text or '- No languages detected'}

## README excerpt
{readme or 'No README file found.'}

## Suggested onboarding steps
1. Read the README and project setup instructions.
2. Review dependency/configuration files.
3. Identify the application entry point.
4. Explore major modules and their imports.
5. Run the existing test suite before making changes.

## Limitations
This report is generated from repository files and static metadata. It is not a complete semantic or runtime analysis.
"""
    return {"report": report, "files": index_info["files"]}
