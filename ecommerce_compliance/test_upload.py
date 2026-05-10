import requests

url = "http://127.0.0.1:8000/api/inspect"
files = {'file': ('input.xlsx', open('input.xlsx', 'rb'), 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')}
data = {'keywords': '다이어트, 최고'}

response = requests.post(url, files=files, data=data)
print(response.status_code)
print(response.text)
