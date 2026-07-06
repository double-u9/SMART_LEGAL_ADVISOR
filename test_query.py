import requests

url = "http://localhost:8000/api/query"
data = {"question": "وفقاً للقانون المدني العراقي رقم 40 لسنة 1951، متى تبدأ شخصية الإنسان ومتى تنتهي؟"}

response = requests.post(url, json=data, stream=True)
for line in response.iter_lines():
    if line:
        print(line.decode('utf-8'))
