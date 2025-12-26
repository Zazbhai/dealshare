# Add User Script Guide

The `add_user.py` script allows you to create users and admins directly from the command line.

## Prerequisites

1. MongoDB must be running
2. Python dependencies installed (`pip install -r requirements.txt`)

## Basic Usage

### Create an Admin User

```bash
python add_user.py --username admin --password admin123 --role admin
```

### Create a Regular User

```bash
python add_user.py --username user1 --password pass123
```

### Create a User with API Key

```bash
python add_user.py --username user1 --password pass123 --api-key YOUR_API_KEY
```

### Create a User with All Settings

```bash
python add_user.py --username user2 --password pass123 --role user \
    --api-url https://api.temporasms.com/stubs/handler_api.php \
    --api-key KEY123 \
    --country-code 22 --operator 1 --service pfk
```

## Interactive Mode

Use `--interactive` or `-i` to be prompted for missing fields:

```bash
python add_user.py --username user3 --role user --interactive
```

This will prompt you for:
- Password (with confirmation)
- API Key (optional)
- API URL (optional)
- Country Code (optional)
- Operator (optional)
- Service (optional)

## Command Line Options

| Option | Short | Required | Default | Description |
|--------|-------|----------|---------|-------------|
| `--username` | `-u` | ✅ Yes | - | Username for the new user |
| `--password` | `-p` | ⚠️ Conditional | - | Password (required unless using `--interactive`) |
| `--role` | `-r` | No | `user` | User role: `user` or `admin` |
| `--api-url` | - | No | `https://api.temporasms.com/stubs/handler_api.php` | API URL |
| `--api-key` | `-k` | No | - | API Key for the user |
| `--country-code` | `-c` | No | `22` | Country code |
| `--operator` | `-o` | No | `1` | Operator |
| `--service` | `-s` | No | `pfk` | Service |
| `--interactive` | `-i` | No | - | Interactive mode - prompt for missing fields |

## Examples

### Example 1: Quick Admin Creation

```bash
python add_user.py -u admin -p admin123 -r admin
```

### Example 2: Create User with Custom Settings

```bash
python add_user.py \
    --username john \
    --password secret123 \
    --api-key abc123xyz \
    --country-code 22 \
    --operator 2 \
    --service pfk
```

### Example 3: Interactive Mode

```bash
python add_user.py --username jane --interactive
```

You'll be prompted:
```
Enter password: 
Confirm password: 
API Key (press Enter to skip): 
API URL (default: https://api.temporasms.com/stubs/handler_api.php): 
Country Code (default: 22): 
Operator (default: 1): 
Service (default: pfk): 
```

## Error Handling

The script will check:
- ✅ MongoDB connection status
- ✅ Username availability (prevents duplicates)
- ✅ Password confirmation (in interactive mode)

## Output

On success:
```
📝 Creating user user: john
   API URL: https://api.temporasms.com/stubs/handler_api.php
   Country: 22, Operator: 1, Service: pfk

✅ User 'john' created successfully!
   Role: user
   User ID: 507f1f77bcf86cd799439011
   API Key: abc123xyz...
```

On error:
```
❌ Failed to create user: Username already exists
```

## Troubleshooting

### MongoDB Not Connected

If you see:
```
❌ MongoDB is not connected!
   Please start MongoDB service: net start MongoDB
```

**Solution:** Start MongoDB:
```bash
# Windows
net start MongoDB

# Or manually
mongod --dbpath C:\data\db
```

### Username Already Exists

If the username is taken, choose a different username or delete the existing user first.

## Security Notes

- Passwords are hashed using bcrypt before storage
- Passwords are never displayed in output
- API keys are partially masked in output (first 10 characters only)

