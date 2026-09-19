import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))
from modules.module3_llm_rag.vector_store import get_collection

col = get_collection()
print("Total documents in ChromaDB:", col.count())
results = col.get()
metadatas = results.get('metadatas', [])
reports = set()
for m in metadatas:
    if m and m.get('rapport'):
        reports.add(m.get('rapport'))

print("Unique reports in ChromaDB:")
for r in sorted(list(reports)):
    print("-", r)
