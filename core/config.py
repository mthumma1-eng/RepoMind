from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data" / "repositories"
DATA_DIR.mkdir(parents=True, exist_ok=True)

APP_NAME = "Codebase Intelligence"
MAX_FILES = 2500
MAX_FILE_BYTES = 750_000
MAX_TOTAL_BYTES = 80_000_000
CHUNK_LINES = 80
CHUNK_OVERLAP = 12

IGNORED_DIRS = {
    ".git", ".venv", "venv", "__pycache__", "node_modules",
    "dist", "build", ".next", ".idea", ".vscode", "coverage",
    "vendor", ".tox", ".mypy_cache", ".pytest_cache"
}
SUPPORTED_EXTENSIONS = {
    ".py", ".js", ".jsx", ".ts", ".tsx", ".java", ".go", ".rs",
    ".cs", ".cpp", ".c", ".php", ".rb", ".html", ".css", ".sql",
    ".md", ".txt", ".json", ".yaml", ".yml", ".toml"
}
LANGUAGES = {
    ".py": "python", ".js": "javascript", ".jsx": "javascript",
    ".ts": "typescript", ".tsx": "typescript", ".java": "java",
    ".go": "go", ".rs": "rust", ".cs": "csharp", ".cpp": "cpp",
    ".c": "c", ".php": "php", ".rb": "ruby", ".html": "html",
    ".css": "css", ".sql": "sql", ".md": "markdown", ".txt": "text",
    ".json": "json", ".yaml": "yaml", ".yml": "yaml", ".toml": "toml"
}
