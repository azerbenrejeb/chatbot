import requests

url = "https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQEFQkW53eix-75n-ZUg2htY1H5BPcDuEH_4xfwErasbf8EnSb5Mw126SAZAMFWW1It9svcC6_AHVeGOI_ZcmH96E7O_fbFDR8J31oE8ch7qE6G7XuBSq-6aysLLMQorARzmeRzRDsIx5XzqK-gQdWDLnJIh3HAuzm8pjUXJHdbk"
try:
    r = requests.get(url, timeout=10)
    print("Status:", r.status_code)
    print("Headers:", r.headers)
    print("Content (first 500 chars):", r.text[:500])
except Exception as e:
    print("Error:", e)
