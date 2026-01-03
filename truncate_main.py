with open('main.py', 'r', encoding='utf-8', errors='replace') as f:
    lines = f.readlines()[:456]

with open('main.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)

print("File truncated successfully")
