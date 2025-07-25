import os
import time
import logging
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from dotenv import load_dotenv
import imaplib
import email

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('Rule1Auth')

load_dotenv()

class Rule1Auth:
    """
    Handles authentication for Rule1Toolbox including login and email verification.
    """
    
    def __init__(self, driver):
        """
        Initialize the Rule1Auth with a browser driver.
        
        Args:
            driver: Selenium WebDriver instance
        """
        self.driver = driver
        self.wait = WebDriverWait(self.driver, 10)
        # Get email verification timeout from .env or use default
        self.verification_timeout = int(os.getenv("EMAIL_VERIFICATION_TIMEOUT", 180))
        self.max_retries = int(os.getenv("EMAIL_VERIFICATION_RETRIES", 3))
        
    def login(self, auto_verify=True):
        """
        Log in to Rule1Toolbox.
        
        Args:
            auto_verify (bool): Whether to automatically verify email code
            
        Returns:
            bool: True if login successful, False otherwise
        """
        email = os.getenv("RULE1_EMAIL")
        if not email:
            logger.error("Missing RULE1_EMAIL in .env")
            raise ValueError("Missing RULE1_EMAIL in .env")

        logger.info("Opening login page...")
        print("Opening login page...")
        self.driver.get("https://ruleonetoolbox.com/login")
        time.sleep(2)

        try:
            email_input = self.driver.find_element(By.XPATH, '//input[@placeholder="Email Address"]')
            email_input.clear()
            email_input.send_keys(email)
            logger.info(f"Entered email: {email}")
            print(f"Entered email: {email}")
        except NoSuchElementException as e:
            logger.error(f"Email input error: {e}")
            print(f"Email input error: {e}")
            return False

        try:
            login_btn = self.wait.until(
                EC.element_to_be_clickable((By.XPATH, '//button[.//span[text()="Log In To Toolbox"]]'))
            )
            login_btn.click()
            logger.info("Clicked login button")
            print("Clicked login button")
        except (TimeoutException, NoSuchElementException) as e:
            logger.error(f"Login button error: {e}")
            print(f"Login button error: {e}")
            return False
            
        # Handle email verification
        if auto_verify:
            verification_success = self._handle_auto_verification()
            if not verification_success:
                logger.warning("Automatic verification failed, falling back to manual verification")
                print("Automatic verification failed, falling back to manual verification")
                verification_code = input("Enter the email verification code manually: ")
                verification_success = self._enter_verification_code(verification_code)
        else:
            logger.info("Manual verification mode selected")
            print("Manual verification mode selected")
            verification_code = input("Enter the email verification code manually: ")
            verification_success = self._enter_verification_code(verification_code)
            
        if not verification_success:
            logger.error("Verification failed")
            print("Verification failed")
            return False

        try:
            # Try multiple selectors for dashboard elements
            dashboard_selectors = [
                '//a[contains(@href, "/explore/guru-portfolio")]',
                '//a[contains(@href, "/dashboard")]',
                '//div[contains(@class, "dashboard")]',
                '//h1[contains(text(), "Dashboard") or contains(text(), "Welcome")]',
                '//div[contains(@class, "logged-in")]'
            ]
            
            for selector in dashboard_selectors:
                try:
                    self.wait.until(
                        EC.presence_of_element_located((By.XPATH, selector))
                    )
                    logger.info(f"Login successful, dashboard loaded with selector: {selector}")
                    print("Login successful, dashboard loaded.")
                    return True
                except TimeoutException:
                    continue
                    
            # If we didn't find any dashboard elements, check if the URL changed
            current_url = self.driver.current_url
            if "login" not in current_url.lower():
                logger.info(f"Login might be successful, URL changed to: {current_url}")
                print("Login successful, dashboard loaded.")
                return True
                
            logger.error("Login failed, could not find dashboard elements")
            print("Login failed, could not find dashboard elements")
            return False
        except TimeoutException as e:
            logger.error(f"Login failed or took too long: {e}")
            print(f"Login failed or took too long: {e}")
            return False
    
    def _handle_auto_verification(self):
        """
        Handle automatic email verification with retries.
        
        Returns:
            bool: True if verification successful, False otherwise
        """
        logger.info(f"Starting automatic verification (timeout: {self.verification_timeout}s, retries: {self.max_retries})")
        print(f"Starting automatic verification (timeout: {self.verification_timeout}s, retries: {self.max_retries})")
        
        for attempt in range(1, self.max_retries + 1):
            logger.info(f"Verification attempt {attempt}/{self.max_retries}")
            print(f"Verification attempt {attempt}/{self.max_retries}")
            
            verification_code = self._get_verification_code(timeout=self.verification_timeout)
            if verification_code:
                # Try to enter the verification code
                if self._enter_verification_code(verification_code):
                    # Wait a moment to see if we get redirected to the dashboard
                    try:
                        time.sleep(3)  # Give the page time to process and redirect
                        
                        # Try multiple selectors for dashboard elements
                        dashboard_selectors = [
                            '//a[contains(@href, "/explore/guru-portfolio")]',
                            '//a[contains(@href, "/dashboard")]',
                            '//div[contains(@class, "dashboard")]',
                            '//h1[contains(text(), "Dashboard") or contains(text(), "Welcome")]',
                            '//div[contains(@class, "logged-in")]'
                        ]
                        
                        for selector in dashboard_selectors:
                            try:
                                self.driver.find_element(By.XPATH, selector)
                                logger.info(f"Verification successful, found dashboard element with selector: {selector}")
                                print(f"Verification successful, found dashboard element")
                                return True
                            except NoSuchElementException:
                                continue
                                
                        # If we didn't find any dashboard elements, check if the URL changed
                        current_url = self.driver.current_url
                        if "login" not in current_url.lower():
                            logger.info(f"Verification might be successful, URL changed to: {current_url}")
                            print(f"Verification might be successful, URL changed")
                            return True
                            
                        logger.warning("Entered code but not redirected to dashboard, may need to try again")
                        print("Entered code but not redirected to dashboard, may need to try again")
                        # Continue to next attempt if we're not on the dashboard yet
                    except Exception as e:
                        logger.warning(f"Error checking for successful verification: {e}")
                        print(f"Error checking for successful verification: {e}")
                        # Continue to next attempt
                else:
                    logger.warning(f"Failed to enter verification code: {verification_code}")
                    print(f"Failed to enter verification code: {verification_code}")
                    
            # If we reach here, verification failed or code entry failed
            if attempt < self.max_retries:
                logger.info(f"Retrying verification in 5 seconds...")
                print(f"Retrying verification in 5 seconds...")
                time.sleep(5)
        
        logger.error(f"All {self.max_retries} verification attempts failed")
        print(f"All {self.max_retries} verification attempts failed")
        return False
            
    def _enter_verification_code(self, verification_code):
        """
        Enter the verification code into the input fields.
        
        Args:
            verification_code (str): The 6-digit verification code
            
        Returns:
            bool: True if code entered successfully, False otherwise
        """
        if not verification_code or len(verification_code) != 6:
            logger.error(f"Invalid verification code: {verification_code}")
            print(f"Invalid verification code: {verification_code}")
            return False
            
        try:
            # First try to find a single input field for the entire code
            try:
                code_input = self.wait.until(
                    EC.presence_of_element_located((By.XPATH, '//input[@type="text" and contains(@class, "verification-code")]'))
                )
                code_input.clear()
                code_input.send_keys(verification_code)
                logger.info("Entered verification code in single field successfully")
                print("Entered verification code in single field successfully")
                
                # Wait a moment for the verification to process
                time.sleep(2)
                
                # No need to click a button - the verification happens automatically
                print("✅ Verification code entered, waiting for processing...")
                logger.info("Verification code entered, waiting for processing...")
                
                return True
            except (TimeoutException, NoSuchElementException):
                # If single field not found, try individual digit inputs
                logger.info("Single verification code field not found, trying individual inputs")
                print("Single verification code field not found, trying individual inputs")
                
                # Try multiple different selectors for OTP input fields
                selectors = [
                    # Common selectors for OTP input fields
                    '//input[@type="text" and @inputmode="numeric"]',
                    '//input[@type="number" and @inputmode="numeric"]',
                    '//input[@type="tel"]',
                    '//input[contains(@class, "otp-input")]',
                    '//input[contains(@class, "code-input")]',
                    # More generic selectors as fallbacks
                    '//div[contains(@class, "otp") or contains(@class, "verification")]//input',
                    '//form//input[@type="text" or @type="tel" or @type="number"]'
                ]
                
                code_inputs = None
                for selector in selectors:
                    try:
                        potential_inputs = self.driver.find_elements(By.XPATH, selector)
                        if len(potential_inputs) == 6:
                            code_inputs = potential_inputs
                            logger.info(f"Found 6 input fields using selector: {selector}")
                            print(f"Found 6 input fields using selector: {selector}")
                            break
                    except Exception as e:
                        logger.debug(f"Selector {selector} failed: {e}")
                
                if not code_inputs:
                    # Last resort: try to find any 6 consecutive input fields
                    try:
                        all_inputs = self.driver.find_elements(By.TAG_NAME, 'input')
                        # Look for 6 consecutive inputs that might be for OTP
                        for i in range(len(all_inputs) - 5):
                            potential_otp_inputs = all_inputs[i:i+6]
                            # Check if these inputs look like they could be OTP fields
                            if all(inp.get_attribute('type') in ['text', 'tel', 'number', ''] for inp in potential_otp_inputs):
                                code_inputs = potential_otp_inputs
                                logger.info("Found 6 consecutive input fields that might be OTP inputs")
                                print("Found 6 consecutive input fields that might be OTP inputs")
                                break
                    except Exception as e:
                        logger.debug(f"Failed to find inputs by tag name: {e}")
                
                if code_inputs and len(code_inputs) == 6:
                    for i, digit in enumerate(verification_code):
                        try:
                            # Try to clear the field first (might not be necessary for some OTP inputs)
                            try:
                                code_inputs[i].clear()
                            except:
                                pass
                            
                            # Send the digit
                            code_inputs[i].send_keys(digit)
                            logger.debug(f"Entered digit {digit} in field {i+1}")
                            time.sleep(0.2)  # Small delay between inputs to prevent race conditions
                        except Exception as e:
                            logger.error(f"Error entering digit {digit} in field {i+1}: {e}")
                            print(f"Error entering digit {digit} in field {i+1}: {e}")
                    
                    logger.info("Entered verification code in multiple fields successfully")
                    print("Entered verification code in multiple fields successfully")
                    
                    # Wait a moment for the verification to process
                    time.sleep(2)
                    
                    # No need to click a button - the verification happens automatically
                    print("✅ Verification code entered, waiting for processing...")
                    logger.info("Verification code entered, waiting for processing...")
                    
                    return True
                else:
                    logger.error(f"Could not find 6 input fields for verification code")
                    print(f"Could not find 6 input fields for verification code")
                    return False
        except (TimeoutException, NoSuchElementException) as e:
            logger.error(f"Verification code input error: {e}")
            print(f"Verification code input error: {e}")
            return False
            
    def _get_verification_code(self, timeout=None):
        """
        Wait for and extract verification code from email.
        
        Args:
            timeout (int): Maximum time to wait for email in seconds
            
        Returns:
            str: Verification code or None if not found
        """
        if timeout is None:
            timeout = self.verification_timeout
            
        # Import the enhanced email reader function that can click 'Send Again'
        from utils.email_reader import wait_for_new_verification_email
        
        # Use the enhanced email reader that can click 'Send Again'
        return wait_for_new_verification_email(timeout=timeout, driver=self.driver)
        
    def _get_latest_email_uid(self, mail):
        """Get the UID of the latest email in the inbox."""
        try:
            mail.select("inbox")
            result, data = mail.uid("search", None, "ALL")
            if result == "OK" and data[0]:
                uids = data[0].split()
                return uids[-1]
        except Exception as e:
            logger.error(f"Error getting latest email UID: {e}")
        return None
        
    def _extract_verification_code(self, msg):
        """Extract 6-digit verification code from email message."""
        try:
            if msg.is_multipart():
                for part in msg.walk():
                    content_type = part.get_content_type()
                    if content_type == "text/plain":
                        body = part.get_payload(decode=True).decode()
                        break
                else:
                    logger.warning("No text/plain part found in multipart email")
                    return None
            else:
                body = msg.get_payload(decode=True).decode()

            logger.debug("Parsing email body for verification code")
            
            # First, try to find the code on the same line as "passcode is:"
            for line in body.splitlines():
                if "passcode is:" in line.lower():
                    digits = ''.join(filter(str.isdigit, line))
                    if len(digits) == 6:
                        return digits
                    else:
                        logger.warning(f"Found passcode line but couldn't extract 6 digits: {line}")
                        # The code might be on the next line, so let's check the lines
                        lines = body.splitlines()
                        for i, current_line in enumerate(lines):
                            if "passcode is:" in current_line.lower() and i + 1 < len(lines):
                                # Check the next line for a 6-digit code
                                next_line = lines[i + 1]
                                digits = ''.join(filter(str.isdigit, next_line))
                                if len(digits) == 6:
                                    logger.info(f"Found verification code on the next line: {digits}")
                                    return digits
            
            # If we haven't found the code yet, try to find any 6-digit number in the email
            for line in body.splitlines():
                digits = ''.join(filter(str.isdigit, line))
                if len(digits) == 6:
                    logger.info(f"Found 6-digit code in email: {digits}")
                    return digits
            
            logger.warning("No verification code found in email body")
            return None
        except Exception as e:
            logger.error(f"Error extracting verification code: {e}")
            return None