import glob
from pathlib import Path

def search_files(pattern):
    print(f"Searching for files containing '{pattern}':")
    for path in Path("c:/RSE Time/chatbot").rglob("*.py"):
        if path.is_file() and not "__pycache__" in str(path) and not ".gemini" in str(path) and not "scratch" in str(path):
            try:
                content = path.read_text(encoding="utf-8")
                if pattern in content:
                    print(f"Found in {path}")
                    # Print lines
                    for idx, line in enumerate(content.splitlines()):
                        if pattern in line:
                            print(f"  {idx+1}: {line}")
            except Exception as e:
                pass

search_files("indicateurs_esg")
print()
search_files("reference_gri")
print()
search_files("ner_entities")
