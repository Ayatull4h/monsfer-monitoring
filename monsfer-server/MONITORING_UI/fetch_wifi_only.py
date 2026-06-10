import requests

session = requests.Session()

# Log in first
login_url = "http://127.0.0.1:5105/login"
r = session.get(login_url)

login_data = {
    "username": "admin",
    "password": "admin"
}
r2 = session.post(login_url, data=login_data)

# Fetch /api/wifi/networks
wifi_url = "http://127.0.0.1:5105/api/wifi/networks"
r3 = session.get(wifi_url)
print("WiFi API status:", r3.status_code)
try:
    print("WiFi API Response keys:", r3.json().keys())
    print("WiFi API networks count:", len(r3.json().get("networks", [])))
    print("WiFi API Sample Network:", r3.json().get("networks", [])[0] if r3.json().get("networks") else None)
except Exception as e:
    print("WiFi API error parsing:", e)
