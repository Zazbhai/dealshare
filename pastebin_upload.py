"""
Utility for uploading logs to Pastebin
"""
import requests

PASTEBIN_API_KEY = "dwt91wd_jowrnLErab5WiVh6UZtMmvwG"
PASTEBIN_API_URL = "https://pastebin.com/api/api_post.php"

def upload_to_pastebin(content, title="Worker Log"):
    """
    Upload content to Pastebin and return the URL
    
    Args:
        content: The text content to upload
        title: Title for the paste
        
    Returns:
        str: Pastebin URL if successful, None otherwise
    """
    try:
        data = {
            'api_dev_key': PASTEBIN_API_KEY,
            'api_option': 'paste',
            'api_paste_code': content,
            'api_paste_name': title,
            'api_paste_private': '1',  # 0=public, 1=unlisted, 2=private
            'api_paste_expire_date': '1M'  # Expire after 1 month
        }
        
        response = requests.post(PASTEBIN_API_URL, data=data, timeout=10)
        
        if response.status_code == 200:
            pastebin_url = response.text.strip()
            # Check if it's a valid URL (not an error message)
            if pastebin_url.startswith('http'):
                print(f"✅ Uploaded to Pastebin: {pastebin_url}")
                return pastebin_url
            else:
                print(f"❌ Pastebin API error: {pastebin_url}")
                return None
        else:
            print(f"❌ Pastebin upload failed: HTTP {response.status_code}")
            return None
            
    except Exception as e:
        print(f"❌ Failed to upload to Pastebin: {e}")
        return None

if __name__ == "__main__":
    # Test the upload
    test_content = "This is a test log\nLine 2\nLine 3"
    url = upload_to_pastebin(test_content, "Test Log")
    if url:
        print(f"Success! URL: {url}")
    else:
        print("Upload failed")
