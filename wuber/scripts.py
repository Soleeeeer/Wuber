import requests

token = 'your_access_token'
headers = {
    'Authorization': f'Bearer {token}',
    'Content-Type': 'application/json'
}
data = {
    'chat_type': 'private',
    'participants': [2]
}
response = requests.post('http://127.0.0.1:8000/api/chats/', json=data, headers=headers)
print(response.json())
