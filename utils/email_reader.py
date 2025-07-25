import os
import imaplib
import email
import time
from dotenv import load_dotenv
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

load_dotenv()

EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASS = os.getenv("EMAIL_PASS")
EMAIL_HOST = os.getenv("EMAIL_HOST", "imap.gmail.com")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", 993))

def get_latest_email_uid(mail):
    mail.select("inbox")
    result, data = mail.uid("search", None, "ALL")
    if result == "OK" and data[0]:
        uids = data[0].split()
        return uids[-1]
    return None

def extract_verification_code(msg):
    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            if content_type == "text/plain":
                body = part.get_payload(decode=True).decode()
                break
    else:
        body = msg.get_payload(decode=True).decode()

    print(f"🔍 EMAIL BODY:\n{body}")
    
    # First, try to find the code on the same line as "passcode is:"
    for line in body.splitlines():
        if "passcode is:" in line.lower():
            digits = ''.join(filter(str.isdigit, line))
            if len(digits) == 6:
                return digits
            else:
                print(f"⚠️ Found passcode line but couldn't extract 6 digits: {line}")
                # The code might be on the next line, so let's check the lines
                lines = body.splitlines()
                for i, current_line in enumerate(lines):
                    if "passcode is:" in current_line.lower() and i + 1 < len(lines):
                        # Check the next line for a 6-digit code
                        next_line = lines[i + 1]
                        digits = ''.join(filter(str.isdigit, next_line))
                        if len(digits) == 6:
                            print(f"✅ Found verification code on the next line: {digits}")
                            return digits
    
    # If we haven't found the code yet, try to find any 6-digit number in the email
    for line in body.splitlines():
        digits = ''.join(filter(str.isdigit, line))
        if len(digits) == 6:
            print(f"✅ Found 6-digit code in email: {digits}")
            return digits
            
    print("⚠️ No verification code found in email body")
    return None

def click_send_again_button(driver):
    """
    Attempt to click the 'Send Again' button on the verification page
    
    Args:
        driver: Selenium WebDriver instance
        
    Returns:
        bool: True if button was found and clicked, False otherwise
    """
    try:
        # Try multiple selectors that might match the "Send Again" button
        selectors = [
            "//span[contains(text(), 'Send Again')]",
            "//button[contains(text(), 'Send Again')]",
            "//a[contains(text(), 'Send Again')]",
            "//span[contains(@class, 'text-blue') and contains(text(), 'Send')]",
            "//span[contains(@class, 'cursor-pointer') and contains(text(), 'Send')]"
        ]
        
        for selector in selectors:
            try:
                send_again_button = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.XPATH, selector))
                )
                print("✅ Found 'Send Again' button")
                send_again_button.click()
                print("✅ Clicked 'Send Again' button")
                return True
            except (TimeoutException, NoSuchElementException):
                continue
                
        print("⚠️ Could not find 'Send Again' button with standard selectors")
        
        # Try JavaScript approach as a fallback
        try:
            # Use JavaScript to find and click any element that looks like a "Send Again" button
            js_script = """
            function findSendAgainButton() {
                // Look for elements containing 'Send Again' text
                const elements = Array.from(document.querySelectorAll('*'));
                for (const el of elements) {
                    if (el.textContent && el.textContent.includes('Send Again')) {
                        el.click();
                        return true;
                    }
                }
                
                // Look for elements with blue text and 'Send' text
                const blueElements = Array.from(document.querySelectorAll('.text-blue-300, .text-blue, .cursor-pointer'));
                for (const el of blueElements) {
                    if (el.textContent && el.textContent.includes('Send')) {
                        el.click();
                        return true;
                    }
                }
                
                return false;
            }
            return findSendAgainButton();
            """
            
            result = driver.execute_script(js_script)
            if result:
                print("✅ Found and clicked 'Send Again' button using JavaScript")
                return True
            else:
                print("⚠️ Could not find 'Send Again' button using JavaScript")
                return False
                
        except Exception as js_error:
            print(f"⚠️ JavaScript error when trying to find 'Send Again' button: {js_error}")
            return False
            
    except Exception as e:
        print(f"⚠️ Error trying to click 'Send Again' button: {e}")
        return False

def wait_for_new_verification_email(timeout=180, driver=None):
    """
    Wait for a new verification email and try to click 'Send Again' if timeout occurs
    
    Args:
        timeout (int): Maximum time to wait for email in seconds
        driver (WebDriver): Selenium WebDriver instance to use for clicking 'Send Again'
        
    Returns:
        str or None: Verification code if found, None otherwise
    """
    print(f"📬 Waiting for new verification email (up to {timeout} seconds)...")
    start_time = time.time()
    check_interval = 5  # Check email every 5 seconds
    resend_interval = 60  # Try to resend every 60 seconds if no email arrives
    last_resend_time = 0

    with imaplib.IMAP4_SSL(EMAIL_HOST, EMAIL_PORT) as mail:
        mail.login(EMAIL_USER, EMAIL_PASS)
        last_seen_uid = get_latest_email_uid(mail)

        while time.time() - start_time < timeout:
            # Check if we should try to resend the code
            current_time = time.time()
            elapsed_since_start = current_time - start_time
            elapsed_since_resend = current_time - last_resend_time
            
            # If we've waited more than resend_interval seconds since last resend attempt
            if driver and elapsed_since_resend > resend_interval and elapsed_since_start > 30:
                print(f"⏱️ No email received after {elapsed_since_resend:.0f} seconds, trying to click 'Send Again'")
                if click_send_again_button(driver):
                    last_resend_time = current_time
                    # Reset the last seen UID after requesting a new code
                    last_seen_uid = get_latest_email_uid(mail)
            
            # Check for new emails
            time.sleep(check_interval)
            mail.select("inbox")
            result, data = mail.uid("search", None, "ALL")
            if result != "OK":
                continue

            uids = data[0].split()
            if not uids or uids[-1] == last_seen_uid:
                continue

            latest_uid = uids[-1]
            result, msg_data = mail.uid("fetch", latest_uid, "(RFC822)")
            if result != "OK":
                continue

            raw_email = msg_data[0][1]
            msg = email.message_from_bytes(raw_email)

            if "toolbox" in msg.get("From", "").lower():
                code = extract_verification_code(msg)
                if code:
                    print(f"📩 Found verification code: {code}")
                    return code

        print("❌ No new verification email arrived in time.")
        return None