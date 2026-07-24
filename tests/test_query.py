import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import requests

url = "http://localhost:8000/api/query"
data = {"question": "وفقاً للقانون المدني العراقي رقم 40 لسنة 1951، متى تبدأ شخصية الإنسان ومتى تنتهي؟"}

response = requests.post(url, json=data, stream=True)
with open("output_query.txt", "w", encoding="utf-8") as f:
    for line in response.iter_lines():
        if line:
            f.write(line.decode('utf-8') + "\n")
            print("Received a line...")
print("Done. Saved to output_query.txt")
