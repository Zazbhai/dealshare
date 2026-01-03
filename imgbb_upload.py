"""
Utility for uploading images to imgbb.com
"""
import base64
import requests
import os
import time

IMGBB_API_KEY = "ddd01452fcc0b8c24efe012b1302eadb"  # Replace with your actual imgbb API key

def upload_image_to_imgbb(image_path, max_retries=3, timeout=120):
    """
    Upload an image to imgbb.com with retry logic and return the URL
    
    Args:
        image_path: Path to the image file
        max_retries: Maximum number of retry attempts (default: 3)
        timeout: Request timeout in seconds (default: 120)
        
    Returns:
        URL of the uploaded image, or None if upload failed
    """
    if not os.path.exists(image_path):
        print(f"[ERROR] Image file not found: {image_path}")
        return None
    
    # Read and encode image once
    try:
        with open(image_path, 'rb') as f:
            image_data = base64.b64encode(f.read()).decode('utf-8')
    except Exception as e:
        print(f"[ERROR] Failed to read image file: {e}")
        return None
    
    # Retry logic
    for attempt in range(1, max_retries + 1):
        try:
            if attempt > 1:
                # Exponential backoff: wait 2^attempt seconds
                wait_time = 2 ** attempt
                print(f"[INFO] Retrying imgbb upload (attempt {attempt}/{max_retries}) after {wait_time} seconds...")
                time.sleep(wait_time)
            
            # Upload to imgbb
            response = requests.post(
                'https://api.imgbb.com/1/upload',
                data={
                    'key': IMGBB_API_KEY,
                    'image': image_data
                },
                timeout=timeout
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    image_url = result['data']['url']
                    if attempt > 1:
                        print(f"[INFO] Image uploaded successfully on attempt {attempt}: {image_url}")
                    else:
                        print(f"[INFO] Image uploaded successfully: {image_url}")
                    return image_url
                else:
                    error_msg = result.get('error', 'Unknown error')
                    print(f"[ERROR] Imgbb upload failed: {error_msg}")
                    # Don't retry on API errors (non-timeout errors)
                    return None
            else:
                print(f"[ERROR] Imgbb API returned status {response.status_code}: {response.text[:200]}")
                # Don't retry on HTTP errors (non-timeout errors)
                return None
                
        except requests.exceptions.Timeout as e:
            print(f"[WARNING] Upload timeout on attempt {attempt}/{max_retries}: {e}")
            if attempt == max_retries:
                print(f"[ERROR] All {max_retries} upload attempts timed out")
                return None
            # Continue to retry on timeout
            continue
            
        except requests.exceptions.RequestException as e:
            print(f"[WARNING] Request error on attempt {attempt}/{max_retries}: {e}")
            if attempt == max_retries:
                print(f"[ERROR] All {max_retries} upload attempts failed")
                return None
            # Continue to retry on request errors
            continue
            
        except Exception as e:
            print(f"[ERROR] Unexpected error during upload (attempt {attempt}/{max_retries}): {e}")
            if attempt == max_retries:
                import traceback
                traceback.print_exc()
                return None
            # Continue to retry on unexpected errors
            continue
    
    return None
if __name__ == "__main__":
    upload_image_to_imgbb(image_path="order_failed.png")






