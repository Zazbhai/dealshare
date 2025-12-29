"""
Utility for uploading images to imgbb.com
"""
import base64
import requests
import os

IMGBB_API_KEY = "a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6"  # Replace with your actual imgbb API key

def upload_image_to_imgbb(image_path):
    """
    Upload an image to imgbb.com and return the URL
    
    Args:
        image_path: Path to the image file
        
    Returns:
        URL of the uploaded image, or None if upload failed
    """
    if not os.path.exists(image_path):
        print(f"[ERROR] Image file not found: {image_path}")
        return None
    
    try:
        # Read and encode image
        with open(image_path, 'rb') as f:
            image_data = base64.b64encode(f.read()).decode('utf-8')
        
        # Upload to imgbb
        response = requests.post(
            'https://api.imgbb.com/1/upload',
            data={
                'key': IMGBB_API_KEY,
                'image': image_data
            },
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                image_url = result['data']['url']
                print(f"[INFO] Image uploaded successfully: {image_url}")
                return image_url
            else:
                print(f"[ERROR] Imgbb upload failed: {result.get('error', 'Unknown error')}")
                return None
        else:
            print(f"[ERROR] Imgbb API returned status {response.status_code}: {response.text}")
            return None
            
    except Exception as e:
        print(f"[ERROR] Failed to upload image to imgbb: {e}")
        import traceback
        traceback.print_exc()
        return None



