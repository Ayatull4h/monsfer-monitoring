import hashlib, json

with open('monsfer-server/db/userdata.json', 'r') as f:
    data = json.load(f)

admin = data['admin']
stored = admin['password']
salt = admin.get('salt', '')
print(f'Stored hash: {stored}')
print(f'Salt: {salt}')

for pw in ['admin123', 'admin', '3kom', '3KOM', 'password', 'Admin123', 'admin1234', '3kom123', 'Admin@123']:
    h = hashlib.sha256((pw + salt).encode()).hexdigest()
    match = '*** MATCH ***' if h == stored else ''
    print(f'{pw} -> {h[:20]}... {match}')
