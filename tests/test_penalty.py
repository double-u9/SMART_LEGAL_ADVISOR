import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import requests
import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

url = "http://localhost:8000/api/query"
payload = {
    "question": "ما عقوبه اي مسؤول بالشركه يقوم باعطاء معلومات غير صحيحه للجهه رسميه",
    "stream": False
}

try:
    response = requests.post(url, json=payload)
    response.raise_for_status()
    data = response.json()
    print(json.dumps(data, ensure_ascii=False, indent=2))
except Exception as e:
    print(f"Error: {e}")
