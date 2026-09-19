import requests

url = "https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/dummy.pdf"
try:
    r = requests.get(url, timeout=10)
    print("Status:", r.status_code)
    print("Length:", len(r.content))
except Exception as e:
    print("Error:", e)
