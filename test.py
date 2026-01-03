from playwright.sync_api import sync_playwright, TimeoutError, Error as PlaywrightError
import time
import os
import sys
import csv
from datetime import datetime
from api_dynamic import get_number, get_otp, cancel_number, set_status
# Try to import imgbb uploader
try:
    from imgbb_upload import upload_image_to_imgbb
except ImportError:
    print("⚠️ imgbb_upload module not found. Screenshot upload will be skipped.")
    def upload_image_to_imgbb(path): return "UPLOAD_FAILED_MODULE_MISSING"



# =========================
# HELPERS
# =========================
def js_click(page, locator):
    if locator.count() == 0:
        return False
    page.evaluate("(el) => el.click()", locator.first)
    return True


def robust_click(page, selector, method="selector"):
    """Try multiple click methods until one works"""
    if method == "selector":
        locator = page.locator(selector)
    else:
        locator = selector  # Already a locator
    
    try:
        locator.scroll_into_view_if_needed()
        time.sleep(0.3)
    except:
        pass
    
    # Try 1: Regular click
    try:
        locator.click(timeout=3000)
        return True
    except:
        pass
    
    # Try 2: Force click
    try:
        locator.click(force=True, timeout=3000)
        return True
    except:
        pass
    
    # Try 3: JS click
    try:
        page.evaluate("(el) => el.click()", locator.first)
        return True
    except:
        pass
    
    return False


# =========================
# LOCATION
# =========================
def select_location(page, search_query=None, location_text_to_select=None):
    """Handles location selection flow"""
    
    # Get values from environment variables if not provided
    if search_query is None:
        search_query = os.environ.get('SEARCH_INPUT', 'chinu juice center')
    if location_text_to_select is None:
        location_text_to_select = os.environ.get('LOCATION_TEXT', 'Chinu Juice Center, Jaswant Nagar, mod, Khatipura, Jaipur, Rajasthan, India')

    try:
        # Click "Type Manually"
        page.wait_for_selector("button:has-text('Type Manually')", timeout=7000)
        page.click("button:has-text('Type Manually')")

        # Search location
        search_input = page.locator("input#google-search")
        search_input.wait_for()
        search_input.fill(search_query)
        print(f"🔍 Searching for location: {search_query}")

        # Select exact location
        print(f"📍 Selecting location: {location_text_to_select}")
        page.wait_for_selector(f"text={location_text_to_select}", timeout=7000)
        page.click(f"text={location_text_to_select}")

        # Confirm delivery
        page.wait_for_selector("button:has-text('Confirm Delivery Location')", timeout=7000)
        page.click("button:has-text('Confirm Delivery Location')")
        print("✅ Confirm Address pressed!")
    except (PlaywrightError, Exception) as e:
        error_msg = str(e)
        if "Target page" in error_msg or "TargetClosedError" in error_msg or "has been closed" in error_msg:
            print(f"❌ Location selection failed: Page/context/browser was closed")
            raise Exception("Page closed during location selection")
        else:
            print(f"❌ Location selection error: {error_msg}")
            raise

def click_user_icon(page):
    """Robust user icon clicking with multiple fallbacks"""
    print("👤 Attempting to click user icon...")
    
    # Wait for page to stabilize
    time.sleep(2)
    
    success = False
    user_icon = None
    
    # Try to find the user icon with multiple selectors
    selectors = [
        "div.UserOptions_userContainer__CqX1R",
        "div[class*='UserOptions_userContainer']",
        "div[class*='userContainer']",
        "button:has-text('Login')",
        "span:has-text('Login')"
    ]
    
    for selector in selectors:
        try:
            if page.locator(selector).count() > 0:
                user_icon = page.locator(selector).first
                print(f"✅ Found user icon with selector: {selector}")
                break
        except:
            continue
    
    if not user_icon:
        print("❌ Could not find user icon")
        page.screenshot(path="user_icon_not_found.png")
        raise Exception("User icon not found")
    
    # Wait for element to be ready
    try:
        user_icon.wait_for(state="visible", timeout=10000)
    except:
        print("⚠️ User icon not visible, trying anyway...")
    
    # Scroll into view
    try:
        user_icon.scroll_into_view_if_needed()
        time.sleep(0.5)
    except:
        pass
    
    # Method 1: Regular click
    try:
        user_icon.click(timeout=3000)
        success = True
        print("✅ User icon clicked (regular)")
    except:
        pass
    
    # Method 2: Force click
    if not success:
        try:
            user_icon.click(force=True, timeout=3000)
            success = True
            print("✅ User icon clicked (force)")
        except:
            pass
    
    # Method 3: JS click
    if not success:
        try:
            page.evaluate("(el) => el.click()", user_icon)
            success = True
            print("✅ User icon clicked (JS)")
        except:
            pass
    
    # Method 4: Dispatch click event
    if not success:
        try:
            user_icon.dispatch_event("click")
            success = True
            print("✅ User icon clicked (dispatch)")
        except:
            pass
    
    if not success:
        print("❌ All click methods failed for user icon")
        page.screenshot(path="user_icon_click_failed.png")
        raise Exception("Could not click user icon")
    
    time.sleep(1)

# =========================
# LOGIN ICON
# =========================
def click_user_icon_with_retry(page, max_attempts=3):
    """Click user icon with retries"""
    for attempt in range(max_attempts):
        try:
            print(f"📍 Attempt {attempt + 1}/{max_attempts}")
            click_user_icon(page)
            return True
        except Exception as e:
            if attempt < max_attempts - 1:
                print(f"⚠️ Attempt failed, retrying... ({e})")
                time.sleep(2)
            else:
                print(f"❌ All attempts failed: {e}")
                raise
    return False
# =========================
# CART FLOW
# =========================
def proceed_to_checkout(page):
    time.sleep(1)

    # CASE 1: Drawer checkout
    drawer_btn = page.locator("button:has-text('Proceed')")
    if drawer_btn.count() > 0:
        print("➡ Proceeding via drawer")
        js_click(page, drawer_btn)
        return

    # CASE 2: Full cart page
    cart_btn = page.locator("button.AddToCart_cartButton__tWwqP")
    if cart_btn.count() > 0:
        print("➡ Proceeding via cart page")
        js_click(page, cart_btn)
        return

    raise Exception("❌ No checkout button found")


def click_add_button(page):
    """Improved ADD button clicking with multiple fallbacks"""
    print("🔘 Attempting to click ADD button...")
    
    # Wait for button to be ready
    page.wait_for_selector(
        ".ActionSection_container__ertTt button.add-button",
        state="visible",
        timeout=30000
    )
    
    # Additional wait for any animations
    time.sleep(1.5)
    
    # Get the button locator
    add_btn = page.locator(".ActionSection_container__ertTt button.add-button").first
    
    # Ensure it's scrolled into view
    try:
        add_btn.scroll_into_view_if_needed()
        time.sleep(0.5)
    except:
        pass
    
    # Try multiple click methods
    success = False
    
    # Method 1: Click the container
    try:
        container = page.locator(".ActionSection_container__ertTt").first
        container.click(timeout=3000)
        success = True
        print("✅ ADD clicked via container")
    except:
        pass
    
    # Method 2: Click button directly
    if not success:
        try:
            add_btn.click(timeout=3000)
            success = True
            print("✅ ADD clicked directly")
        except:
            pass
    
    # Method 3: Force click
    if not success:
        try:
            add_btn.click(force=True)
            success = True
            print("✅ ADD clicked (forced)")
        except:
            pass
    
    # Method 4: JS click
    if not success:
        try:
            page.evaluate("(el) => el.click()", add_btn)
            success = True
            print("✅ ADD clicked (JS)")
        except Exception as e:
            print(f"❌ All ADD click methods failed: {e}")
            page.screenshot(path="add_button_failed.png")
            raise
    
    time.sleep(1)

def add_product_and_check_cart(page, product_url, quantity=1, request_id=None, api_key=None, api_url=None):
    """
    Add product to cart with specified quantity and check for removal notice and OOS
    Returns True if cart is ready to proceed, False if needs retry with different product
    """
    print(f"🛒 Opening product page: {product_url}")
    try:
        page.goto(product_url, timeout=45000)
    except Exception as e:
        print(f"⚠️ Failed to load page: {e}")
        return False
        
    time.sleep(1)

    # -----------------------------
    # FAST OOS CHECK
    # -----------------------------
    # Check for immediate "Out of Stock" indicators
    oos_indicators = ["Currently Unavailable", "Notify Me", "Out of Stock", "Sold Out"]
    for indicator in oos_indicators:
        if page.locator(f"text={indicator}").count() > 0:
            if page.locator(f"text={indicator}").first.is_visible():
                print(f"⚠️ Product is Out of Stock ('{indicator}' detected)")
                return False

    # -----------------------------
    # ADD TO CART
    # -----------------------------
    try:
        click_add_button(page)
        print("✅ Added to cart (initially)")
    except Exception as e:
        print(f"⚠️ Failed to click Add button (likely OOS or page changed): {e}")
        return False

    time.sleep(2)

    # -----------------------------
    # QUANTITY ADJUSTMENT
    # -----------------------------
    if quantity > 1:
        print(f"🔢 Adjusting quantity to {quantity}...")
        
        # Click plus button (quantity - 1) times since we already have 1 item
        plus_icon = page.locator("img[alt='plus'][src*='plus']")
        
        for i in range(quantity - 1):
            try:
                # Wait for plus button to be visible
                plus_icon.wait_for(state="visible", timeout=5000)
                
                # Try multiple click methods
                success = False
                
                # Method 1: Regular click
                try:
                    plus_icon.first.click(timeout=3000)
                    success = True
                except:
                    pass
                
                # Method 2: Force click
                if not success:
                    try:
                        plus_icon.first.click(force=True)
                        success = True
                    except:
                        pass
                
                # Method 3: JS click
                if not success:
                    try:
                        page.evaluate("(el) => el.click()", plus_icon.first)
                        success = True
                    except:
                        pass
                
                if success:
                    print(f"  ➕ Clicked plus button (iteration {i+1}/{quantity-1})")
                    time.sleep(0.5)  # Small delay between clicks
                else:
                    print(f"  ⚠️ Failed to click plus button on iteration {i+1}")
                    
            except Exception as e:
                print(f"  ⚠️ Error clicking plus button: {e}")
                break
        
        # Verify quantity
        time.sleep(1)
        try:
            quantity_text = page.locator("span.AddButton_quantity-text__enpVI").first
            actual_quantity = quantity_text.text_content().strip()
            
            if actual_quantity == str(quantity):
                print(f"✅ Quantity verified: {actual_quantity} (expected: {quantity})")
            else:
                print(f"⚠️ Quantity mismatch: got {actual_quantity}, expected {quantity}")
                print("   Continuing anyway...")
        except Exception as e:
            print(f"⚠️ Could not verify quantity: {e}")

    time.sleep(1)

    # -----------------------------
    # CART CHECK
    # -----------------------------
    print("🛍️ Opening cart...")
    try:
        page.locator("img[src*='bag']").first.click(force=True)
        print("✅ Clicked bag icon")
    except Exception as e:
        print(f"⚠️ Failed to click bag icon: {e}")
        return False
        
    time.sleep(2)

    # Check if login button appears after opening bag
    login_btn_selectors = [
        "button:has-text('Login')",
        "button:has-text('Log in')",
        "button:has-text('Sign in')",
        "span:has-text('Login')"
    ]
    
    for selector in login_btn_selectors:
        try:
            login_btn = page.locator(selector)
            if login_btn.count() > 0 and login_btn.first.is_visible():
                print(f"🔐 Login button found after opening bag! Clicking it...")
                if robust_click(page, login_btn.first, method="locator"):
                    print("✅ Login button clicked successfully")
                    time.sleep(5)  # Wait for a few seconds
                    
                    # Request a new OTP using the same request_id if available
                    if request_id and api_key and api_url:
                        print("🔄 Requesting a new OTP...")
                        try:
                            set_status(3, request_id, api_key, api_url)  # Status 3 = request new OTP
                            print("✅ New OTP request sent")
                            
                            # Wait a bit for OTP to arrive
                            time.sleep(3)
                            
                            # Get the new OTP
                            print("⏳ Getting new OTP (max 2 minutes)...")
                            new_otp = get_otp(
                                request_id=request_id,
                                api_key=api_key,
                                base_url=api_url,
                                timeout_seconds=120.0,
                                poll_interval=2.0
                            )
                            
                            if new_otp:
                                print(f"✅ Got new OTP: {new_otp}")
                                
                                # Enter the new OTP
                                otp_boxes = page.locator("input[type='tel'][maxlength='1']")
                                # Clear existing OTP
                                for i in range(6):  # Assuming 6 digit OTP
                                    try:
                                        otp_boxes.nth(i).fill("")
                                    except:
                                        pass
                                
                                # Fill new OTP
                                for i, digit in enumerate(new_otp):
                                    otp_boxes.nth(i).fill(digit)
                                time.sleep(1)
                                
                                # Click Verify OTP button
                                print("🔘 Clicking Verify OTP button...")
                                verify_btn = page.locator("button.Button_button__8B4nB.Button_active__8l_7k", has_text="Verify OTP")
                                
                                try:
                                    verify_btn.wait_for(state="visible", timeout=5000)
                                except:
                                    print("⚠️ Verify button not visible, trying anyway...")
                                
                                time.sleep(0.5)
                                
                                # Try multiple click methods
                                success = False
                                try:
                                    verify_btn.click(timeout=3000)
                                    success = True
                                    print("✅ Verify OTP clicked (regular)")
                                except:
                                    pass
                                
                                if not success:
                                    try:
                                        verify_btn.click(force=True, timeout=3000)
                                        success = True
                                        print("✅ Verify OTP clicked (force)")
                                    except:
                                        pass
                                
                                if not success:
                                    try:
                                        page.evaluate("(el) => el.click()", verify_btn.first)
                                        success = True
                                        print("✅ Verify OTP clicked (JS)")
                                    except:
                                        pass
                                
                                if not success:
                                    if robust_click(page, verify_btn, method="locator"):
                                        success = True
                                        print("✅ Verify OTP clicked (robust)")
                                
                                if not success:
                                    print("❌ Failed to click Verify OTP button")
                                    page.screenshot(path="verify_otp_failed.png")
                                
                                time.sleep(2)
                            else:
                                print("❌ Failed to get new OTP within 2 minutes")
                        except Exception as e:
                            print(f"⚠️ Error requesting/getting new OTP: {e}")
                    
                    time.sleep(2)
                    # After clicking login, the cart should reload - break and continue
                    break
                else:
                    print("⚠️ Failed to click login button, continuing anyway...")
        except Exception as e:
            pass

    # Check for "Remove Items & Proceed" text
    remove_text_options = [
        "Remove Items & Proceed",
        "Remove Items",
        "Remove Item & Proceed",
        "Remove Item"
    ]
    
    for text in remove_text_options:
        if page.locator(f"text={text}").count() > 0:
            if page.locator(f"text={text}").first.is_visible():
                print(f"⚠️ Found '{text}' - Product needs to be removed (Delivery not available)")
                
                # Try to cleanly remove it before failing, so next product has clean slate? 
                # Actually, better to just fail and let next product flow handle its own state, 
                # but clicking remove is safer to clear the bad state.
                try:
                    remove_btn = page.locator(f"text={text}").first
                    if robust_click(page, remove_btn, method="locator"):
                        print("✅ Clicked remove button to clear bad state")
                        time.sleep(1)
                except:
                    pass
                
                return False  # Return False because this product failed
            
    return True  # Return True if no removal needed

def add_product_only(page, product_url, quantity=1):
    """
    Add product to cart with specified quantity WITHOUT opening cart
    Returns True if product was added successfully, False if failed
    """
    print(f"🛒 Opening product page: {product_url}")
    try:
        page.goto(product_url, timeout=45000)
    except Exception as e:
        print(f"⚠️ Failed to load page: {e}")
        return False
        
    time.sleep(1)

    # -----------------------------
    # FAST OOS CHECK
    # -----------------------------
    # Check for immediate "Out of Stock" indicators
    oos_indicators = ["Currently Unavailable", "Notify Me", "Out of Stock", "Sold Out"]
    for indicator in oos_indicators:
        if page.locator(f"text={indicator}").count() > 0:
            if page.locator(f"text={indicator}").first.is_visible():
                print(f"⚠️ Product is Out of Stock ('{indicator}' detected)")
                return False

    # -----------------------------
    # ADD TO CART
    # -----------------------------
    try:
        click_add_button(page)
        print("✅ Added to cart")
    except Exception as e:
        print(f"⚠️ Failed to click Add button (likely OOS or page changed): {e}")
        return False

    time.sleep(2)

    # -----------------------------
    # QUANTITY ADJUSTMENT
    # -----------------------------
    if quantity > 1:
        print(f"🔢 Adjusting quantity to {quantity}...")
        
        # Click plus button (quantity - 1) times since we already have 1 item
        plus_icon = page.locator("img[alt='plus'][src*='plus']")
        
        for i in range(quantity - 1):
            try:
                # Wait for plus button to be visible
                plus_icon.wait_for(state="visible", timeout=5000)
                
                # Try multiple click methods
                success = False
                
                # Method 1: Regular click
                try:
                    plus_icon.first.click(timeout=3000)
                    success = True
                except:
                    pass
                
                # Method 2: Force click
                if not success:
                    try:
                        plus_icon.first.click(force=True)
                        success = True
                    except:
                        pass
                
                # Method 3: JS click
                if not success:
                    try:
                        page.evaluate("(el) => el.click()", plus_icon.first)
                        success = True
                    except:
                        pass
                
                if success:
                    print(f"  ➕ Clicked plus button (iteration {i+1}/{quantity-1})")
                    time.sleep(0.5)  # Small delay between clicks
                else:
                    print(f"  ⚠️ Failed to click plus button on iteration {i+1}")
                    
            except Exception as e:
                print(f"  ⚠️ Error clicking plus button: {e}")
                break
        
        # Verify quantity
        time.sleep(1)
        try:
            quantity_text = page.locator("span.AddButton_quantity-text__enpVI").first
            actual_quantity = quantity_text.text_content().strip()
            
            if actual_quantity == str(quantity):
                print(f"✅ Quantity verified: {actual_quantity} (expected: {quantity})")
            else:
                print(f"⚠️ Quantity mismatch: got {actual_quantity}, expected {quantity}")
                print("   Continuing anyway...")
        except Exception as e:
            print(f"⚠️ Could not verify quantity: {e}")

    time.sleep(1)
    return True

def check_cart_for_errors(page, request_id=None, api_key=None, api_url=None):
    """
    Open cart and check for errors (login button, remove items, etc.)
    Returns True if cart is ready to proceed, False if errors found
    """
    print("🛍️ Opening cart to check for errors...")
    try:
        page.locator("img[src*='bag']").first.click(force=True)
        print("✅ Clicked bag icon")
    except Exception as e:
        print(f"⚠️ Failed to click bag icon: {e}")
        return False
        
    time.sleep(2)

    # Check if login button appears after opening bag
    login_btn_selectors = [
        "button:has-text('Login')",
        "button:has-text('Log in')",
        "button:has-text('Sign in')",
        "span:has-text('Login')"
    ]
    
    for selector in login_btn_selectors:
        try:
            login_btn = page.locator(selector)
            if login_btn.count() > 0 and login_btn.first.is_visible():
                print(f"🔐 Login button found after opening bag! Clicking it...")
                if robust_click(page, login_btn.first, method="locator"):
                    print("✅ Login button clicked successfully")
                    time.sleep(5)  # Wait for a few seconds
                    
                    # Request a new OTP using the same request_id if available
                    if request_id and api_key and api_url:
                        print("🔄 Requesting a new OTP...")
                        try:
                            from api_dynamic import set_status, get_otp
                            set_status(3, request_id, api_key, api_url)  # Status 3 = request new OTP
                            print("✅ New OTP request sent")
                            
                            # Wait a bit for OTP to arrive
                            time.sleep(3)
                            
                            # Get the new OTP
                            print("⏳ Getting new OTP (max 2 minutes)...")
                            new_otp = get_otp(
                                request_id=request_id,
                                api_key=api_key,
                                base_url=api_url,
                                timeout_seconds=120.0,
                                poll_interval=2.0
                            )
                            
                            if new_otp:
                                print(f"✅ Got new OTP: {new_otp}")
                                
                                # Enter the new OTP
                                otp_boxes = page.locator("input[type='tel'][maxlength='1']")
                                # Clear existing OTP
                                for i in range(6):  # Assuming 6 digit OTP
                                    try:
                                        otp_boxes.nth(i).fill("")
                                    except:
                                        pass
                                
                                # Fill new OTP
                                for i, digit in enumerate(new_otp):
                                    otp_boxes.nth(i).fill(digit)
                                time.sleep(1)
                                
                                # Click Verify OTP button
                                print("🔘 Clicking Verify OTP button...")
                                verify_btn = page.locator("button.Button_button__8B4nB.Button_active__8l_7k", has_text="Verify OTP")
                                
                                try:
                                    verify_btn.wait_for(state="visible", timeout=5000)
                                except:
                                    print("⚠️ Verify button not visible, trying anyway...")
                                
                                time.sleep(0.5)
                                
                                # Try multiple click methods
                                success = False
                                try:
                                    verify_btn.click(timeout=3000)
                                    success = True
                                    print("✅ Verify OTP clicked (regular)")
                                except:
                                    pass
                                
                                if not success:
                                    try:
                                        verify_btn.click(force=True, timeout=3000)
                                        success = True
                                        print("✅ Verify OTP clicked (force)")
                                    except:
                                        pass
                                
                                if not success:
                                    try:
                                        page.evaluate("(el) => el.click()", verify_btn.first)
                                        success = True
                                        print("✅ Verify OTP clicked (JS)")
                                    except:
                                        pass
                                
                                if not success:
                                    if robust_click(page, verify_btn, method="locator"):
                                        success = True
                                        print("✅ Verify OTP clicked (robust)")
                                
                                if not success:
                                    print("❌ Failed to click Verify OTP button")
                                    page.screenshot(path="verify_otp_failed.png")
                                
                                time.sleep(2)
                            else:
                                print("❌ Failed to get new OTP within 2 minutes")
                        except Exception as e:
                            print(f"⚠️ Error requesting/getting new OTP: {e}")
                    
                    time.sleep(2)
                    # After clicking login, the cart should reload - break and continue
                    break
                else:
                    print("⚠️ Failed to click login button, continuing anyway...")
        except Exception as e:
            pass

    # Check for "Remove Items & Proceed" text
    remove_text_options = [
        "Remove Items & Proceed",
        "Remove Items",
        "Remove Item & Proceed",
        "Remove Item"
    ]
    
    for text in remove_text_options:
        if page.locator(f"text={text}").count() > 0:
            if page.locator(f"text={text}").first.is_visible():
                print(f"⚠️ Found '{text}' - Product needs to be removed (Delivery not available)")
                return False  # Return False because error found
            
    return True  # Return True if no errors found
# =========================
# MAIN
# =========================
def main():
     with sync_playwright() as p:
        # Launch browser with optimized settings for parallel execution
        # Added explicit stability arguments to prevent crashes in parallel mode
        try:
            browser_args = [
                '--disable-blink-features=AutomationControlled',
                '--disable-dev-shm-usage',  # Key for reducing memory crashes in parallel execution
                '--disable-gpu',
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-web-security',
                '--disable-features=IsolateOrigins,site-per-process',
            ]
            
            browser = p.chromium.launch(
                headless=False,  # Run in visible mode for local development
                slow_mo=0,  # No delay for better performance
                args=browser_args
            )
        except Exception as e:
            print(f"❌ CRITICAL: Failed to launch browser: {e}")
            sys.exit(1)

        # Get location settings from environment
        latitude = float(os.environ.get('LATITUDE', '26.994880'))
        longitude = float(os.environ.get('LONGITUDE', '75.774836'))
        should_select_location = os.environ.get('SELECT_LOCATION', '1') == '1'
        
        context = browser.new_context(
            geolocation={"latitude": latitude, "longitude": longitude},
            permissions=["geolocation"]
        )

        page = context.new_page()
        page.goto("https://www.dealshare.in/", timeout=60000)
        time.sleep(2)

        # -----------------------------
        # LOCATION
        # -----------------------------
        if should_select_location:
            # Get location search settings from environment
            search_input = os.environ.get('SEARCH_INPUT', 'chinu juice center')
            location_text = os.environ.get('LOCATION_TEXT', 'Chinu Juice Center, Jaswant Nagar, mod, Khatipura, Jaipur, Rajasthan, India')
            
            print(f"📍 Location selection enabled")
            print(f"   Search query: {search_input}")
            print(f"   Location text: {location_text}")
            
            try:
                print("➡ Trying normal location flow...")
                select_location(page, search_input, location_text)
            except (TimeoutError, PlaywrightError, Exception) as e:
                error_msg = str(e)
                if "Page closed" in error_msg or "TargetClosedError" in error_msg or "has been closed" in error_msg:
                    print(f"❌ Location selection failed: Page was closed. Cannot continue.")
                    raise
                
                print(f"⚠ Location selection failed, retrying... Error: {error_msg}")
                try:
                    # Click address bar fallback
                    page.wait_for_selector("p.Address_addressBold__GlDKW", timeout=8000)
                    page.click("p.Address_addressBold__GlDKW")
                    time.sleep(1)
                    select_location(page, search_input, location_text)
                except (TimeoutError, PlaywrightError, Exception) as retry_error:
                    print(f"❌ Location selection retry also failed: {retry_error}")
                    raise
        else:
            print("⏭️ Location selection step skipped (disabled in settings)")


        # -----------------------------
        # LOGIN
        # -----------------------------
        time.sleep(2)
        click_user_icon_with_retry(page)

        
        

        # Get phone number from API
       
        
        phone_number = "9262231588"
       
        
        # Enter phone number
        phone_input = page.locator("input[placeholder='Ex 9876543210']")
        phone_input.wait_for()
        phone_input.fill(phone_number)
        phone_input.press("Enter")

        # Wait a bit for OTP to be sent
        print("⏳ Waiting for OTP (max 2 minutes)...")
        time.sleep(3)
        
        # Get OTP from API (wait for 2 minutes)
        otp = input("Enter Otp: ")
        
     
        
        # OTP received - enter it
        print(f"✅ Got OTP: {otp}")
        otp_boxes = page.locator("input[type='tel'][maxlength='1']")
        for i, digit in enumerate(otp):
            otp_boxes.nth(i).fill(digit)
        time.sleep(1)
            
            # Click Verify OTP button
        print("🔘 Clicking Verify OTP button...")
        verify_btn = page.locator("button.Button_button__8B4nB.Button_active__8l_7k", has_text="Verify OTP")
            
        # Wait for button to be visible and enabled
        try:
            verify_btn.wait_for(state="visible", timeout=5000)
        except:
            print("⚠️ Verify button not visible, trying anyway...")
            
        time.sleep(0.5)
            
            # Try multiple click methods for verify button
        success = False
            
            # Method 1: Regular click
        try:
            verify_btn.click(timeout=3000)
            success = True
            print("✅ Verify OTP clicked (regular)")
        except:
                pass
            
            # Method 2: Force click
        if not success:
                try:
                    verify_btn.click(force=True, timeout=3000)
                    success = True
                    print("✅ Verify OTP clicked (force)")
                except:
                    pass
            
            # Method 3: JS click
        if not success:
                try:
                    page.evaluate("(el) => el.click()", verify_btn.first)
                    success = True
                    print("✅ Verify OTP clicked (JS)")
                except:
                    pass
            
            # Method 4: Use robust_click helper
        if not success:
                if robust_click(page, verify_btn, method="locator"):
                    success = True
                    print("✅ Verify OTP clicked (robust)")
            
        if not success:
                print("❌ Failed to click Verify OTP button")
                page.screenshot(path="verify_otp_failed.png")
            
        time.sleep(1.5)
        print("✅ LOGIN SUCCESSFUL")

        # -----------------------------
        # PRODUCT SYSTEM
        # -----------------------------
        # Try to get products from JSON (new format), fall back to old format
        product_urls = []
        product_quantities = []
        
        products_json = os.environ.get('PRODUCTS_JSON', '')
        if products_json:
            try:
                import json
                products = json.loads(products_json)
                for product in products:
                    url = product.get('url', '').strip()
                    quantity = int(product.get('quantity', 1))
                    if url:
                        product_urls.append(url)
                        product_quantities.append(quantity)
            except Exception as e:
                print(f"⚠️ Failed to parse PRODUCTS_JSON: {e}, falling back to old format")
        
        # Fall back to old format if no products from JSON
        if len(product_urls) == 0:
            primary_product_url = os.environ.get('PRIMARY_PRODUCT_URL', '').strip()
            secondary_product_url = os.environ.get('SECONDARY_PRODUCT_URL', '').strip()
            third_product_url = os.environ.get('THIRD_PRODUCT_URL', '').strip()
            primary_product_quantity = int(os.environ.get('PRIMARY_PRODUCT_QUANTITY', '1'))
            secondary_product_quantity = int(os.environ.get('SECONDARY_PRODUCT_QUANTITY', '1'))
            third_product_quantity = int(os.environ.get('THIRD_PRODUCT_QUANTITY', '1'))
            
            if primary_product_url:
                product_urls.append(primary_product_url)
                product_quantities.append(primary_product_quantity)
            if secondary_product_url:
                product_urls.append(secondary_product_url)
                product_quantities.append(secondary_product_quantity)
            if third_product_url:
                product_urls.append(third_product_url)
                product_quantities.append(third_product_quantity)
        
        # Validate at least one product URL
        if len(product_urls) == 0:
            print("❌ At least one product URL is required but not configured")
            browser.close()
            sys.exit(1)  # Exit with generic error code
        
        print(f"📋 Found {len(product_urls)} product URLs to try")
        print(f"🔢 Quantities: {product_quantities}")
        
        # Check if ORDER_ALL mode is enabled
        order_all = os.environ.get('ORDER_ALL', '0') == '1'
        
        cart_success = False
        
        if order_all:
            # ORDER ALL MODE: Add all products first, then check cart once
            print("🛒 ORDER ALL mode enabled - Adding all products...")
        else:
            # FALLBACK MODE: Try adding each product one by one (without opening bag)
            print("🛒 FALLBACK mode - Adding products one by one...")
        
        # Both modes now work the same: add all products, then check cart at the end
        all_added = True
        
        for i, (url, quantity) in enumerate(zip(product_urls, product_quantities)):
            print(f"🔄 [Product {i+1}/{len(product_urls)}] Adding: {url} (quantity: {quantity})")
            
            try:
                if not add_product_only(page, url, quantity):
                    print(f"⚠️ Failed to add product {i+1}")
                    all_added = False
                    break
                else:
                    print(f"✅ Product {i+1} added successfully")
            except Exception as e:
                print(f"❌ Error adding product {i+1}: {e}")
                all_added = False
                break
        
        if not all_added:
            print("❌ Failed to add all products - Closing windows")
            page.screenshot(path="all_products_failed.png")
            browser.close()
            sys.exit(5)  # SPECIAL EXIT CODE 5 -> SIGNALS WORKER MANAGER TO STOP ALL WORKERS
        
        # After adding all products, open bag and check for errors
        print("✅ All products added. Opening bag and checking for errors...")
        if not check_cart_for_errors(page, request_id, api_key, api_url):
            print("⚠️ Cart check found errors (remove_text_options detected) - Closing windows")
            page.screenshot(path="cart_errors_found.png")
            browser.close()
            sys.exit(5)  # Exit with code 5 to signal worker manager to stop
        
        print("✅ Cart check passed - ready to proceed")
        
        time.sleep(1)

        btn = page.locator("button.AddToCart_cartButton__tWwqP")
        btn.wait_for(state="visible", timeout=15000)
        btn.click(force=True)
        print("✅ Proceed to pay clicked")
        time.sleep(2)

        # -----------------------------
        # ADDRESS
        # -----------------------------
        print("📝 Filling address details...")
        
        # Get order details from environment variables
        automation_name = os.environ.get('AUTOMATION_NAME', '')
        automation_house_flat = os.environ.get('AUTOMATION_HOUSE_FLAT', '')
        automation_landmark = os.environ.get('AUTOMATION_LANDMARK', '')
        
        print(f"[DEBUG] Order details from environment:")
        print(f"[DEBUG]   Name: {automation_name}")
        print(f"[DEBUG]   House/Flat: {automation_house_flat}")
        print(f"[DEBUG]   Landmark: {automation_landmark}")
        
        if not automation_name or not automation_house_flat or not automation_landmark:
            print("❌ Order details (name, house/flat, landmark) are required but not configured")
            browser.close()
            sys.exit(1)
        
        # Wait for form to be visible
        page.wait_for_selector("input[name='userName']", state="visible", timeout=10000)
        time.sleep(1)

        # Fill name
        name_input = page.locator("input[name='userName']")
        name_input.fill(automation_name)
        print(f"✅ Filled name: {automation_name}")
        time.sleep(0.5)

        # Fill flat
        flat_input = page.locator("input[name='flat']")
        flat_input.fill(automation_house_flat)
        print(f"✅ Filled house/flat: {automation_house_flat}")
        time.sleep(0.5)

        # Fill landmark
        landmark_input = page.locator("input[name='landMark']")
        landmark_input.fill(automation_landmark)
        print(f"✅ Filled landmark: {automation_landmark}")
        time.sleep(1)

        # Save address with robust clicking
        print("💾 Saving address...")
        
        # Use text selector to get the correct button
        save_btn = page.locator("button.btn.btn-secondary", has_text="Save Address")
        
        # Wait for button to be visible and enabled
        save_btn.wait_for(state="visible", timeout=5000)
        time.sleep(0.5)
        
        # Try multiple click methods
        if robust_click(page, save_btn, method="locator"):
            print("✅ Address saved successfully")
        else:
            print("❌ Failed to save address")
            page.screenshot(path="address_save_failed.png")
            raise Exception("Could not save address")
        
        time.sleep(3)

        # -----------------------------
        # PAYMENT
        # -----------------------------
        print("💳 Selecting payment method...")
        
        # Wait for payment options to load
        page.wait_for_selector("div.Payment_methodItem__BLz7I", timeout=10000)
        time.sleep(1)
        
        # Click Cash on Delivery
        cod_option = page.locator(
            "div.Payment_methodItem__BLz7I",
            has_text="Cash on Delivery"
        ).first
        
        cod_option.scroll_into_view_if_needed()
        cod_option.click(force=True)
        print("✅ COD selected")
        time.sleep(2)

        print("📦 Attempting to place order...")
        
        # Try multiple selectors for the place order button
        place_btn = None
        
        # Selector 1: Class name
        if page.locator("button.CodView_orderButton__E53_u").count() > 0:
            place_btn = page.locator("button.CodView_orderButton__E53_u").first
            print("Found button via class")
        
        # Selector 2: Text content
        elif page.locator("button:has-text('Place Order')").count() > 0:
            place_btn = page.locator("button:has-text('Place Order')").first
            print("Found button via text")
        
        # Selector 3: Any button in COD view
        elif page.locator("button[type='button']").count() > 0:
            place_btn = page.locator("button[type='button']").last
            print("Found button via type")
        
        if place_btn:
            # Wait for button to be ready
            try:
                place_btn.wait_for(state="visible", timeout=5000)
            except:
                print("⚠️ Button not visible, trying anyway...")
            
            # Scroll into view
            try:
                place_btn.scroll_into_view_if_needed()
                time.sleep(1)
            except:
                pass
            
            # Try clicking with multiple methods
            success = False
            
            # Method 1: Regular click
            try:
                place_btn.click(timeout=5000)
                success = True
                print("✅ Place order clicked (regular)")
            except Exception as e:
                print(f"Regular click failed: {e}")
            
            # Method 2: Force click
            if not success:
                try:
                    place_btn.click(force=True, timeout=5000)
                    success = True
                    print("✅ Place order clicked (force)")
                except Exception as e:
                    print(f"Force click failed: {e}")
            
            # Method 3: JS click
            if not success:
                try:
                    page.evaluate("(el) => el.click()", place_btn)
                    success = True
                    print("✅ Place order clicked (JS)")
                except Exception as e:
                    print(f"JS click failed: {e}")
            
            # Method 4: Dispatch click event
            if not success:
                try:
                    place_btn.dispatch_event("click")
                    success = True
                    print("✅ Place order clicked (dispatch)")
                except Exception as e:
                    print(f"Dispatch click failed: {e}")
            
            if success:
                print("🎉 PLACE ORDER TRIGGERED - MARKING SUCCESS")
                # Wait briefly to check for immediate error (e.g. backend failure toast)
                time.sleep(2)
                
                # Take screenshot immediately regardless of outcome
                screenshot_filename = f"order_result_{int(time.time())}.png"
                try:
                    page.screenshot(path=screenshot_filename)
                    print(f"📸 Screenshot taken: {screenshot_filename}")
                except Exception as e:
                    print(f"⚠️ Failed to take screenshot: {e}")
                    screenshot_filename = None

                # Check for common error texts
                error_texts = ["Something went wrong", "Out of Stock", "Not available", "Sold Out"]
                error_found = False
                error_reason = ""
                for txt in error_texts:
                    if page.locator(f"text={txt}").count() > 0:
                        if page.locator(f"text={txt}").first.is_visible():
                            print(f"❌ Error detected after place order: {txt}")
                            error_found = True
                            error_reason = txt
                            break
                
                # Determine status
                status = "Success" if not error_found else f"Failed - {error_reason}"
                
                # Upload and Log
                screenshot_url = "N/A"
                if screenshot_filename:
                    print("☁️ Uploading screenshot to ImgBB...")
                    uploaded_url = upload_image_to_imgbb(screenshot_filename)
                    if uploaded_url:
                        screenshot_url = uploaded_url
                        print(f"✅ Screenshot uploaded: {screenshot_url}")
                    else:
                        print("⚠️ Screenshot upload failed")
                        screenshot_url = "UPLOAD_FAILED"
                
                # Log to CSV
                try:
                    csv_file = "my_orders.csv"
                    file_exists = os.path.isfile(csv_file)
                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    
                    with open(csv_file, mode='a', newline='', encoding='utf-8') as f:
                        writer = csv.writer(f)
                        if not file_exists:
                            writer.writerow(["Timestamp", "Screenshot URL", "Status"])
                        writer.writerow([timestamp, screenshot_url, status])
                    print(f"📝 Order info logged to {csv_file}")
                except Exception as e:
                    print(f"❌ Failed to log to CSV: {e}")

                if not error_found:
                    print("✅ No errors detected after placement.")
                    print("TRIGGER_ORDER_SUCCESS") 
                    browser.close()
                    sys.exit(0) # SUCCESS EXIT
                else:
                    print("❌ Order failed due to post-click error")
                    browser.close()
                    sys.exit(1) # FAIL EXIT
            
            else:
                print("❌ All click methods failed!")
                page.screenshot(path="place_order_failed.png")
                browser.close()
                sys.exit(1)
        else:
            print("❌ Could not find place order button!")
            page.screenshot(path="button_not_found.png")
            browser.close()
            sys.exit(1)
        
        # This should never be reached, but just in case
        browser.close()
        sys.exit(1)


if __name__ == "__main__":
    main()