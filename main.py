from playwright.sync_api import sync_playwright, TimeoutError
import time
import os
from api_dynamic import get_number, get_otp, cancel_number


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


def click_user_icon(page):
    # Wait until the user icon container is visible
    page.wait_for_selector("div.UserOptions_userContainer__CqX1R", timeout=10000)

    # Click the actual clickable container
    page.locator("div.UserOptions_userContainer__CqX1R").first.click(force=True)


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False,
            slow_mo=300
        )

        context = browser.new_context(
            geolocation={"latitude": 26.9124, "longitude": 75.7873},
            permissions=["geolocation"]
        )

        page = context.new_page()
        page.goto("https://www.dealshare.in/", timeout=60000)

        time.sleep(2)

        # -----------------------------
        # LOCATION SELECTION
        # -----------------------------
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

        # -----------------------------
        # LOGIN FLOW
        # -----------------------------
        time.sleep(3)
        click_user_icon(page)
        time.sleep(2)

        # Get API configuration from environment
        api_key = '2ce12168a4f72374207d61fc634ba23c79cf'
        api_url = 'https://api.temporasms.com/stubs/handler_api.php'
        country = '22'
        operator = '10'
        service = 'lmeh'
        
        if not api_key:
            print("❌ API_KEY not found in environment")
            browser.close()
            return
        
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
            return
        
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
            return
        
        # OTP received - enter it
        print(f"✅ Got OTP: {otp}")
        otp_boxes = page.locator("input[type='tel'][maxlength='1']")
        for i, digit in enumerate(otp):
            otp_boxes.nth(i).fill(digit)
        otp_boxes.nth(len(otp) - 1).press("Enter")
        
        # Cancel the number after entering OTP
        print("🔄 Cancelling number after OTP entry...")
        time.sleep(1)
        cancel_result = cancel_number(request_id, api_key, api_url)
        print(f"✅ Number cancelled: {cancel_result}")

        print("✅ LOGIN SUCCESSFUL")
        
        # -------------------------------------------
        # ADD PRODUCT TO CART
        # -------------------------------------------
        print("🛒 Opening product page...")

        page.goto(
            "https://www.dealshare.in/pname/650ml-Hand-Press-Manual-Chopper-%7C-3-Stainless-Steel-Blades,-Push-Chopper-for-Vegetables,-Fruits,-Chilly/pid/BAU4214",
            timeout=60000
        )

        # Click ADD button
        page.wait_for_selector("button.add-button, button.ActionSection_button__LuQRJ", timeout=10000)
        page.click("button.add-button, button.ActionSection_button__LuQRJ")

        print("✅ Product added to cart")

        # -------------------------------------------
        # OPEN CART
        # -------------------------------------------
        page.wait_for_selector("img[src*='bag']", timeout=10000)
        page.click("img[src*='bag']")
        print("Clicked On Bag Icon!")

        # -------------------------------------------
        # ADD DELIVERY ADDRESS
        # -------------------------------------------
        time.sleep(4)
        btn = page.locator("button.AddToCart_cartButton__tWwqP")
        btn.wait_for(state="visible", timeout=15000)
        btn.scroll_into_view_if_needed()
        btn.click(force=True)
        print("Procced To Pay Cliked!")
        time.sleep(2)

        # Fill address form
        import os
        name = os.environ.get('AUTOMATION_NAME', 'Zaza Yagami')
        house_flat = os.environ.get('AUTOMATION_HOUSE_FLAT', 'Ward 32')
        landmark = os.environ.get('AUTOMATION_LANDMARK', 'Chinu Juice Center')

        page.wait_for_selector("input[placeholder='Name']", timeout=10000)
        page.fill("input[placeholder='Name']", name)

        page.fill("input[placeholder='House / Flat No.']", house_flat)
        page.fill("input[placeholder='Landmark']", landmark)

        # Save address
        page.click("button.btn.btn-secondary")

        print("✅ Address saved")

        # -------------------------------------------
        # SELECT PAYMENT METHOD - COD
        # -------------------------------------------
        page.wait_for_selector("div.Payment_methodItem__BLz7I", timeout=10000)

        # Select COD option
        page.locator("div.Payment_methodItem__BLz7I").filter(
            has_text="Cash on Delivery"
        ).click()

        # Place order
        page.wait_for_selector("button.CodView_orderButton__E53_u", timeout=10000)
        page.click("button.CodView_orderButton__E53_u")

        # -------------------------------------------
        # VERIFY ORDER SUCCESS
        # -------------------------------------------
        page.wait_for_timeout(5000)

        current_url = page.url
        if "order-success" in current_url:
            print("🎉 ORDER SUCCESSFUL")
            page.screenshot(path="order_success.png")
        else:
            print("❌ ORDER FAILED")
            page.screenshot(path="order_failed.png")

        # -------------------------------------------
        # GO TO ORDERS PAGE
        # -------------------------------------------
        page.goto("https://www.dealshare.in/my-orders")

        page.wait_for_selector("div.OrderListingCard_statusContainer__oS_3p", timeout=15000)

        order_card = page.locator("div.OrderListingCard_statusContainer__oS_3p").first
        order_card.click()

        # Extract Order ID
        order_id_elem = page.locator("span:text-matches('Order ID', 'i')")
        order_id_text = order_id_elem.inner_text()

        print(f"🧾 ORDER ID FOUND: {order_id_text}")

        print("✅ FLOW COMPLETED SUCCESSFULLY")

        time.sleep(5)
        browser.close()



if __name__ == "__main__":
    main()
