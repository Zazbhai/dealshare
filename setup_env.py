#!/usr/bin/env python3
"""Script to create .env file with MongoDB Atlas connection"""

import os

env_content = """# MongoDB Atlas Configuration
MONGO_URI=mongodb+srv://dealshare_user:f9CiLYaaozkLdMxb@dealshare.oysqfuf.mongodb.net/dealshare_automation?retryWrites=true&w=majority&appName=dealshare
DB_NAME=dealshare_automation

# JWT Secret Key (Change this in production!)
JWT_SECRET_KEY=your-secret-key-change-in-production-make-it-long-and-random
"""

env_file = '.env'

if os.path.exists(env_file):
    response = input(f"{env_file} already exists. Overwrite? (y/n): ")
    if response.lower() != 'y':
        print("Cancelled.")
        exit(0)

with open(env_file, 'w') as f:
    f.write(env_content)

print(f"[SUCCESS] Created {env_file} file with MongoDB Atlas configuration")
print("\nNow test the connection:")
print("  python check_mongodb.py")

