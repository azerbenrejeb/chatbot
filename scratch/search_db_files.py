from pathlib import Path

for path in Path("c:/RSE Time/chatbot").rglob("*"):
    if path.is_file() and (path.suffix in [".db", ".sqlite", ".sqlite3"] or "db" in path.name.lower()):
        print(path, "size:", path.stat().st_size)
