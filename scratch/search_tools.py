from pathlib import Path

def search_files(pattern):
    print(f"Searching for files containing '{pattern}':")
    for path in Path("c:/RSE Time/chatbot/tools").glob("*.py"):
        try:
            content = path.read_text(encoding="utf-8")
            if pattern in content:
                print(f"Found in {path}")
        except Exception as e:
            pass

search_files("sqlite")
search_files("db")
search_files("database")
search_files("insert")
search_files("INSERT")
search_files("indicateurs")
search_files("conformity")
search_files("reference")
