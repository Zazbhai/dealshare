from playwright.sync_api import sync_playwright, TimeoutError
import time
import os
import sys
from api_dynamic import get_number, get_otp, cancel_number



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
def select_location(page):
    """Handles location selection flow"""

    # Click "Type Manually"
    page.wait_for_selector("button:has-text('Type Manually')", timeout=7000)
    page.click("button:has-text('Type Manually')")

    # Search location
    search_input = page.locator("input#google-search")
    search_input.wait_for()
    search_input.fill("chinu juice center")

    # Select exact location
    location_text = "Chinu Juice Center, Jaswant Nagar, mod, Khatipura, Jaipur, Rajasthan, India"
    page.wait_for_selector(f"text={location_text}", timeout=7000)
    page.click(f"text={location_text}")

    # Confirm delivery
    page.wait_for_selector("button:has-text('Confirm Delivery Location')", timeout=7000)
    page.click("button:has-text('Confirm Delivery Location')")
    print("✅ Confirm Address pressed!")

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

def add_product_and_check_cart(page, product_url):
    """
    Add product to cart and check for removal notice
    Returns True if cart is ready to proceed, False if needs retry with different product
    """
    print(f"🛒 Opening product page: {product_url}")
    page.goto(product_url, timeout=60000)
    time.sleep(1)

    click_add_button(page)
    print("✅ Product added to cart")
    time.sleep(3)

    # -----------------------------
    # CART CHECK
    # -----------------------------
    print("🛍️ Opening cart...")
    page.locator("img[src*='bag']").first.click(force=True)
    print("✅ Clicked bag icon")
    time.sleep(2)

    # Check for "Remove Items & Proceed" text
    remove_text_options = [
        "Remove Items & Proceed",
        "Remove Items",
        "Remove Item & Proceed"
    ]
    
    found_remove_text = False
    for text in remove_text_options:
        if page.locator(f"text={text}").count() > 0:
            print(f"⚠️ Found '{text}' - Product needs to be removed")
            found_remove_text = True
            
            # Click the remove button
            try:
                remove_btn = page.locator(f"text={text}").first
                if robust_click(page, remove_btn, method="locator"):
                    print("✅ Clicked remove button")
                    time.sleep(2)
            except Exception as e:
                print(f"⚠️ Could not click remove button: {e}")
            
            break
    
    return not found_remove_text  # Return True if no removal needed



# =========================
# MAIN
# =========================
def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=300)

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
            try:
                print("➡ Trying normal location flow...")
                select_location(page)
            except TimeoutError:
                print("⚠ Location selection failed, retrying...")

                # Click address bar fallback
                page.wait_for_selector("p.Address_addressBold__GlDKW", timeout=8000)
                page.click("p.Address_addressBold__GlDKW")

                time.sleep(1)
                select_location(page)
        else:
            print("⏭️ Location selection step skipped (disabled in settings)")

        # -----------------------------
        # LOGIN
        # -----------------------------
        time.sleep(2)
        click_user_icon_with_retry(page)

        
        
        # Get API configuration from environment
        api_key = '4ae5f380b71903cdb7b1b55018ed74eab9e7'
        api_url = 'https://api.temporasms.com/stubs/handler_api.php'
        country = '22'
        operator = '10'
        service = 'lmeh'
        
        if not api_key:
            print("❌ API_KEY not found in environment")
            browser.close()
            sys.exit(1)  # Exit with failure code
        
        # Get phone number from API
        print("📱 Requesting phone number from API...")
        number_result = get_number(
            service=service,
            country=country,
            operator=operator,
            api_key=api_key,
            base_url=api_url
        )
        if not number_result:
            print("❌ Failed to get phone number from API")
            browser.close()
            sys.exit(1)  # Exit with failure code
        
        request_id, phone_number = number_result
        print(f"✅ Got phone number: {phone_number} (request_id: {request_id})")
        
        # Enter phone number
        phone_input = page.locator("input[placeholder='Ex 9876543210']")
        phone_input.wait_for()
        phone_input.fill(phone_number)
        phone_input.press("Enter")

        # Wait a bit for OTP to be sent
        print("⏳ Waiting for OTP (max 2 minutes)...")
        time.sleep(3)
        
        # Get OTP from API (wait for 2 minutes)
        otp = get_otp(
            request_id=request_id,
            api_key=api_key,
            base_url=api_url,
            timeout_seconds=120.0,
            poll_interval=2.0
        )
        
        if not otp:
            print("❌ Failed to get OTP within 2 minutes. Cancelling number...")
            cancel_number(request_id, api_key, api_url)
            print("❌ Number cancelled due to OTP timeout")
            browser.close()
            sys.exit(1)  # Exit with failure code
        
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
                   
        
        # Cancel the number after entering OTP
        print("🔄 Cancelling number after OTP entry...")
        time.sleep(1)
        cancel_result = cancel_number(request_id, api_key, api_url)
        print(f"✅ Number cancelled: {cancel_result}")

        print("✅ LOGIN SUCCESSFUL")

        # -----------------------------
        # PRODUCT
        # -----------------------------
        primary_product_url = os.environ.get('PRIMARY_PRODUCT_URL', '')
        secondary_product_url = os.environ.get('SECONDARY_PRODUCT_URL', '')
        third_product_url = os.environ.get('THIRD_PRODUCT_URL', '')
        
        # Primary URL is mandatory - validate it exists
        if not primary_product_url or not primary_product_url.strip():
            print("❌ Primary product URL is required but not configured")
            browser.close()
            sys.exit(1)  # Exit with error code to stop worker
        
        # Build URL list: Primary → Secondary → Third (always in this order)
        product_urls = [primary_product_url]
        if secondary_product_url and secondary_product_url.strip():
            product_urls.append(secondary_product_url)
        if third_product_url and third_product_url.strip():
            product_urls.append(third_product_url)
        
        # Try each URL until one works
        cart_ready = False
        for idx, product_url in enumerate(product_urls):
            try:
                print(f"🛒 Trying product URL {idx + 1}/{len(product_urls)}: {product_url}")
                cart_ready = add_product_and_check_cart(page, product_url)
                if cart_ready:
                    print("✅ Cart is ready to proceed")
                    break
                elif idx < len(product_urls) - 1:
                    print("🔄 Trying next URL...")
            except Exception as e:
                print(f"⚠️ Failed to add product from URL {idx + 1}: {e}")
                if idx < len(product_urls) - 1:
                    print("🔄 Trying next URL...")
                    continue
        
        if not cart_ready:
            print("❌ All product URLs failed - cannot proceed")
            page.screenshot(path="all_products_failed.png")
            browser.close()
            sys.exit(1)  # Exit with error code to stop all workers
        
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
        
        # Wait for form to be visible
        page.wait_for_selector("input[name='userName']", state="visible", timeout=10000)
        time.sleep(1)

        # Fill name
        name_input = page.locator("input[name='userName']")
        name_input.fill("Zaza Yagami")
        time.sleep(0.5)

        # Fill flat
        flat_input = page.locator("input[name='flat']")
        flat_input.fill("Ward 32")
        time.sleep(0.5)

        # Fill landmark
        landmark_input = page.locator("input[name='landMark']")
        landmark_input.fill("Chinu Juice Center")
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
            
            # Check if button is enabled
            try:
                is_enabled = place_btn.is_enabled()
                print(f"Button enabled: {is_enabled}")
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
            
            if not success:
                print("❌ All click methods failed!")
                page.screenshot(path="place_order_failed.png")
        else:
            print("❌ Could not find place order button!")
            page.screenshot(path="button_not_found.png")

        time.sleep(5)

        # -----------------------------
        # VERIFY ORDER
        # -----------------------------
        # Wait for navigation to order success page after place order button is clicked
        print("⏳ Waiting for order confirmation...")
        time.sleep(5)  # Give time for page to navigate
        
        # Check URL multiple times to ensure we get the final URL
        max_checks = 3
        order_successful = False
        current_url = ""
        
        for i in range(max_checks):
            time.sleep(2)
            current_url = page.url
            url_lower = current_url.lower()
            print(f"🔍 Check {i+1}/{max_checks} - Current URL: {current_url}")
            
            # Check if URL contains order-success (case-insensitive)
            if "order-success" in url_lower:
                order_successful = True
                print(f"✅ Order success detected in URL: {current_url}")
                break
        
        if order_successful:
            print("🎉 ORDER SUCCESSFUL!")
            page.screenshot(path="order_success.png")
            browser.close()
            sys.exit(0)  # Exit with success code
        else:
            print("❌ ORDER FAILED")
            print(f"Final URL: {current_url}")
            page.screenshot(path="order_failed.png")
            browser.close()
            sys.exit(1)  # Exit with failure code
        
        # This should never be reached, but just in case
        browser.close()
        sys.exit(1)


if __name__ == "__main__":
    main()