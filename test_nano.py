import requests
import os
import sys

# src dizinini path'e ekle, config'i kullanmak için
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))
from config import get_gemini_llm_api_key

api_key = get_gemini_llm_api_key()

payload = {
    'contents': [{'parts': [{'text': 'A beautiful mountain'}]}],
    'generationConfig': {
        'responseModalities': ['IMAGE'],
        'imageConfig': {'aspectRatio': '9:16'}
    }
}
url = 'https://generativelanguage.googleapis.com/v1beta/models/gemini-3.1-flash-image-preview:generateContent'
res = requests.post(url, headers={'x-goog-api-key': api_key, 'Content-Type': 'application/json'}, json=payload)
print(res.status_code)
print(res.text[:500])
