import os
import sys
import time
import shutil
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait

sys.path.insert(0, os.path.abspath("Milestone1"))
import database

def get_driver():
    opts = Options()
    opts.add_argument("--headless=new")
    opts.add_argument("--window-size=1440,920")
    opts.add_argument("--disable-gpu")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    driver = webdriver.Chrome(options=opts)
    driver.set_window_size(1440, 920)
    return driver

def save_both(driver, filename):
    out1 = os.path.join("screenshots", filename)
    out2 = os.path.join("Milestone1", "screenshots", filename)
    driver.save_screenshot(out1)
    shutil.copy2(out1, out2)
    # also save hyphenated copy
    parts = filename.split("_", 1)
    if len(parts) == 2 and parts[0].isdigit():
        alt_name = parts[1].replace("_", "-")
        shutil.copy2(out1, os.path.join("screenshots", alt_name))
        shutil.copy2(out1, os.path.join("Milestone1", "screenshots", alt_name))
    print(f"Captured: {filename}", flush=True)

def wait_for_streamlit(driver, timeout=10):
    WebDriverWait(driver, timeout).until(
        lambda d: len(d.find_elements(By.CSS_SELECTOR, "div.stApp")) > 0
    )
    time.sleep(1.5)

def fill_input(elem, text):
    elem.send_keys(Keys.CONTROL + "a")
    elem.send_keys(Keys.BACKSPACE)
    elem.send_keys(text)
    elem.send_keys(Keys.TAB)
    time.sleep(0.4)

def get_visible_inputs(driver):
    return [i for i in driver.find_elements(By.CSS_SELECTOR, "div[data-testid='stTextInput'] input") if i.is_displayed()]

def click_sidebar_nav(driver, text):
    labels = driver.find_elements(By.CSS_SELECTOR, "div[data-testid='stRadio'] label")
    for l in labels:
        if text.lower() in l.text.lower():
            l.click()
            time.sleep(1.8)
            return True
    return False

def click_tab(driver, text):
    tabs = driver.find_elements(By.CSS_SELECTOR, "button[role='tab']")
    for t in tabs:
        if text.lower() in t.text.lower():
            t.click()
            time.sleep(1.8)
            return True
    return False

def click_button_with_text(driver, text):
    buttons = [b for b in driver.find_elements(By.CSS_SELECTOR, "button") if b.is_displayed()]
    for b in buttons:
        if text.lower() in b.text.lower():
            b.click()
            time.sleep(1.8)
            return True
    return False

def click_form_submit(driver):
    btns = [b for b in driver.find_elements(By.CSS_SELECTOR, "button[data-testid*='primaryFormSubmit'], button[kind='primaryFormSubmit']") if b.is_displayed()]
    if btns:
        btns[0].click()
        time.sleep(2.5)

def main():
    driver = get_driver()
    try:
        print("Navigating to http://localhost:8501...", flush=True)
        driver.get("http://localhost:8501")
        wait_for_streamlit(driver)

        # 1. Login Page
        click_sidebar_nav(driver, "Login")
        time.sleep(1.2)
        save_both(driver, "01_login_page.png")

        # 2. Registration Page
        click_sidebar_nav(driver, "Signup")
        time.sleep(1.2)
        save_both(driver, "02_registration_page.png")

        # 3. OTP Verification Page (trigger login with partner_demo)
        click_sidebar_nav(driver, "Login")
        time.sleep(1.2)
        inputs = get_visible_inputs(driver)
        fill_input(inputs[0], "partner_demo")
        inputs = get_visible_inputs(driver)
        fill_input(inputs[1], "Franchise@2026!")
        click_form_submit(driver)
        time.sleep(2.0)
        save_both(driver, "03_otp_verification_page.png")

        # 4. Incorrect OTP Error Message ("Invalid OTP. Please try again.")
        otp_inputs = get_visible_inputs(driver)
        if otp_inputs:
            fill_input(otp_inputs[0], "111111")
            click_form_submit(driver)
            time.sleep(2.0)
        save_both(driver, "04_incorrect_otp_error.png")

        # 5. Forgot Password Page (Click Forgot Password button on OTP page)
        click_button_with_text(driver, "Forgot Password?")
        time.sleep(1.8)
        save_both(driver, "05_forgot_password_page.png")

        # 6. Password Reset Page (Route 2: Gmail OTP)
        click_tab(driver, "Gmail OTP")
        time.sleep(1.5)
        email_inputs = get_visible_inputs(driver)
        if email_inputs:
            fill_input(email_inputs[0], "partner@franchise.com")
        click_button_with_text(driver, "Send Recovery OTP")
        time.sleep(2.5)
        save_both(driver, "06_password_reset_page.png")

        # 7. User Dashboard (Login successfully with valid OTP)
        click_button_with_text(driver, "Back to Login")
        time.sleep(1.5)
        inputs = get_visible_inputs(driver)
        fill_input(inputs[0], "partner_demo")
        inputs = get_visible_inputs(driver)
        fill_input(inputs[1], "Franchise@2026!")
        click_form_submit(driver)
        time.sleep(2.0)

        # Retrieve valid OTP from database for partner_demo
        conn = database.get_connection()
        c = conn.cursor()
        c.execute("SELECT otp_code FROM otps WHERE LOWER(email) = 'partner@franchise.com' AND purpose = 'login' AND used = 0 ORDER BY id DESC LIMIT 1")
        row = c.fetchone()
        valid_otp = row["otp_code"] if row else "123456"
        print(f"Retrieved active OTP from DB: {valid_otp}", flush=True)

        otp_inputs = get_visible_inputs(driver)
        if otp_inputs:
            fill_input(otp_inputs[0], valid_otp)
            click_form_submit(driver)
            time.sleep(3.0)
        save_both(driver, "07_user_dashboard.png")

        # 8. Franchise Management Pages (Franchise Outlets Directory)
        click_tab(driver, "Franchise Outlets Directory")
        time.sleep(2.0)
        save_both(driver, "08_franchise_management_page.png")

        # 9. Supply & Inventory Orders Module
        click_tab(driver, "Supply & Inventory Orders")
        time.sleep(2.0)
        save_both(driver, "09_franchise_inventory_orders.png")

        # 10. Franchise Expansion Application Module
        click_tab(driver, "Apply for New Franchise")
        time.sleep(2.0)
        save_both(driver, "10_franchise_application_module.png")

        # 11. Admin Portal Gate
        click_button_with_text(driver, "Logout")
        time.sleep(2.0)
        click_sidebar_nav(driver, "Admin Portal")
        time.sleep(1.8)
        save_both(driver, "11_admin_portal.png")

        # 12. Admin Control Center & Audit Dashboard
        admin_inputs = get_visible_inputs(driver)
        if len(admin_inputs) >= 2:
            fill_input(admin_inputs[0], "admin")
            admin_inputs = get_visible_inputs(driver)
            fill_input(admin_inputs[1], "Admin@Placeholder2026!")
            click_form_submit(driver)
            time.sleep(3.0)
        save_both(driver, "12_admin_dashboard.png")

        # 13. Admin Franchise Network Oversight
        click_tab(driver, "Franchise Network Operations")
        time.sleep(2.0)
        save_both(driver, "13_admin_franchise_network.png")

        print("SUCCESS: Complete screenshot suite captured and synchronized perfectly!", flush=True)

    finally:
        driver.quit()

if __name__ == "__main__":
    main()
