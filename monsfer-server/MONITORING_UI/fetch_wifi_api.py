import requests

session = requests.Session()

# Log in first
login_url = "http://127.0.0.1:5105/login"
# First get to obtain cookies
r = session.get(login_url)

# POST credentials
login_data = {
    "username": "admin",
    "password": "admin"  # Or whatever password is if needed, but since auto_login is active, we just need the cookies
}
r2 = session.post(login_url, data=login_data)
print("Login status:", r2.status_code)

# Now fetch /api/wifi/networks
wifi_url = "http://127.0.0.1:5105/api/wifi/networks"
r3 = session.get(wifi_url)
print("WiFi API status:", r3.status_code)
try:
    print("WiFi API Response JSON:", r3.json())
except Exception as e:
    print("WiFi API Response Text:", r3.text[:1000])

# Now fetch /api/system/health
system_url = "http://127.0.0.1:5105/api/system/health"
r4 = session.get(system_url)
print("System Health API status:", r4.status_code)
try:
    print("System Health API Response JSON:", r4.json())
except Exception as e:
    print("System Health API Response Text:", r4.text[:1000])
