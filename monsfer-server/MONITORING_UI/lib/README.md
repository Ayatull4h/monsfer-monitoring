# Password Handler Module

A simple module for password encoding and verification using hash algorithms.

## Features

- Support for multiple hash algorithms (default: SHA-256)
- Salt support for enhanced security
- Simple encode and decode functions
- Type hints for better IDE support
- Command line interface with multiple commands
- Returns user information (UPT ID, fullname, username, sites) on successful verification

## Installation

No additional dependencies required. Just import the module:

```python
from decode_password import PasswordHandler
```

## Usage

### Command Line Interface

The module can be used directly from the terminal with three main commands:

1. **Encode a password**:
```bash
python decode_password.py encode mypassword -s mysalt
```

2. **Verify a password**:
```bash
python decode_password.py verify stored_hash mypassword -s mysalt
```

3. **Decode from userdata.json**:
```bash
python decode_password.py decode db/userdata.json username password
```

Global options:
- `-a, --algorithm`: Hash algorithm to use (default: sha256)

Command-specific options:
- `-s, --salt`: Salt to use (optional)

### Python Module Usage

```python
# Create password handler instance
handler = PasswordHandler()

# Encode password
password = "mypassword"
salt = "mysalt"
encoded = handler.encode(password, salt)
print(f"Encoded: {encoded}")

# Verify password
is_valid = handler.decode(encoded, password, salt)
print(f"Password valid: {is_valid}")

# Decode from userdata.json
result = handler.decode_from_json('db/userdata.json', 'username', 'password')
if result:
    if isinstance(result, dict):
        if result.get('is_admin'):
            print(f"Admin user: {result['username']}")
        else:
            print(f"UPT ID: {result['id_upt']}")
            print(f"Fullname: {result['fullname']}")
            print(f"Username: {result['username']}")
            print(f"Sites: {result['sites']}")
    else:
        print("Password verified")
else:
    print("Invalid credentials")
```

### With Different Hash Algorithm

```python
# Create instance with custom hash algorithm
handler = PasswordHandler(hash_algorithm='md5')

# Use as normal
encoded = handler.encode('password123', 'salt')
is_valid = handler.decode(encoded, 'password123', 'salt')
```

## Available Methods

1. **Encode Password**
```python
encoded = handler.encode('password123', salt='mysalt')
```

2. **Verify Password**
```python
is_valid = handler.decode(stored_hash, 'password123', salt='mysalt')
```

3. **Decode from JSON**
```python
result = handler.decode_from_json('userdata.json', 'username', 'password')
# Returns:
# - For admin: {'username': username, 'is_admin': True}
# - For UPT: {'id_upt': upt_id, 'fullname': fullname, 'username': username, 'sites': sites}
# - For invalid: False
```

## Example Output

1. **Encode Command**:
```
Password: test123
Salt: mysalt
Algorithm: sha256
Encoded: 1234abcd...
```

2. **Verify Command**:
```
Stored Hash: 1234abcd...
Password: test123
Salt: mysalt
Algorithm: sha256
Result: ✓ Match
```

3. **Decode Command**:
```
Username: jakarta
Password: jakarta123
Result: ✓ Success
UPT ID: 01
Fullname: Balai Monitor Spektrum Frekuensi Radio Kelas I DKI Jakarta
Username: jakarta
Sites: [
    {
        "id_perangkat": "001",
        "site_name": "jakarta",
        "token": "dki"
    },
    ...
]
```

## Security Note

This module is intended for password encoding and verification only. Always use strong passwords and unique salts for enhanced security.

## License

This module is provided as-is under the MIT License. 