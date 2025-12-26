#!/usr/bin/env python3
"""
Script to add users and admins to the database
Usage:
    python add_user.py --username john --password secret123 --role admin
    python add_user.py --username jane --password pass123 --role user --api-key YOUR_API_KEY
"""

import argparse
import sys
import os
from getpass import getpass

# Add parent directory to path to import models
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from models.user import User

def create_user(username, password, role='user', api_url='', api_key=''):
    """Create a new user"""
    result = User.create_user(
        username=username,
        password=password,
        role=role,
        api_url=api_url or 'https://api.temporasms.com/stubs/handler_api.php',
        api_key=api_key
    )
    
    return result

def main():
    parser = argparse.ArgumentParser(
        description='Add users and admins to the database',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Create an admin user
  python add_user.py --username admin --password admin123 --role admin

  # Create a regular user with API key
  python add_user.py --username user1 --password pass123 --api-key YOUR_API_KEY

  # Create a user with API settings
  python add_user.py --username user2 --password pass123 --role user \\
      --api-url https://api.example.com --api-key KEY123

  # Interactive mode (will prompt for password)
  python add_user.py --username user3 --role user
        """
    )
    
    parser.add_argument('--username', '-u', required=True,
                          help='Username for the new user')
    parser.add_argument('--password', '-p',
                          help='Password for the new user (will prompt if not provided)')
    parser.add_argument('--role', '-r', choices=['user', 'admin'], default='user',
                          help='User role (default: user)')
    parser.add_argument('--api-url', 
                          default='https://api.temporasms.com/stubs/handler_api.php',
                          help='API URL (default: https://api.temporasms.com/stubs/handler_api.php)')
    parser.add_argument('--api-key', '-k',
                          help='API Key for the user')
    parser.add_argument('--interactive', '-i', action='store_true',
                          help='Interactive mode - prompt for missing fields')
    
    args = parser.parse_args()
    
    # Get password
    password = args.password
    if not password:
        if args.interactive:
            password = getpass('Enter password: ')
            password_confirm = getpass('Confirm password: ')
            if password != password_confirm:
                print("❌ Passwords do not match!", file=sys.stderr)
                sys.exit(1)
        else:
            print("❌ Password is required. Use --password or --interactive", file=sys.stderr)
            sys.exit(1)
    
    # Interactive mode - prompt for missing optional fields
    if args.interactive:
        if not args.api_key:
            api_key_input = input('API Key (press Enter to skip): ').strip()
            if api_key_input:
                args.api_key = api_key_input
        
        if not args.api_url or args.api_url == 'https://api.temporasms.com/stubs/handler_api.php':
            api_url_input = input(f'API URL (default: {args.api_url}): ').strip()
            if api_url_input:
                args.api_url = api_url_input
    
    # Check if MongoDB is connected
    try:
        from models.user import _db_connected
        if not _db_connected:
            print("❌ MongoDB is not connected!", file=sys.stderr)
            print("   Please start MongoDB service: net start MongoDB", file=sys.stderr)
            print("   Or see start_mongodb.md for instructions", file=sys.stderr)
            sys.exit(1)
    except Exception as e:
        print(f"❌ Error checking database connection: {e}", file=sys.stderr)
        sys.exit(1)
    
    # Create user
    print(f"\n📝 Creating {args.role} user: {args.username}")
    print(f"   API URL: {args.api_url}")
    
    result = create_user(
        username=args.username,
        password=password,
        role=args.role,
        api_url=args.api_url,
        api_key=args.api_key or ''
    )
    
    if result['success']:
        print(f"\n✅ User '{args.username}' created successfully!")
        print(f"   Role: {result['user']['role']}")
        print(f"   User ID: {result['user']['_id']}")
        if args.api_key:
            print(f"   API Key: {args.api_key[:10]}...")
        return 0
    else:
        print(f"\n❌ Failed to create user: {result.get('error', 'Unknown error')}", file=sys.stderr)
        return 1

if __name__ == '__main__':
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  Cancelled by user", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)

