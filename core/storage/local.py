from pathlib import Path


class LocalStorage:
    def __init__(self, root: str) -> None:
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def write_bytes(self, filename: str, content: bytes) -> Path:
        path = self.root / filename
        path.write_bytes(content)
        return path

    def read_text(self, path: str) -> str:
        return Path(path).read_text(encoding="utf-8")
