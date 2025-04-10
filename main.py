from selenium_profiles.webdriver import Chrome
from selenium_profiles.profiles import profiles
from selenium.webdriver.common.by import By
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support import expected_conditions as EC
import argparse
import time
import base64
import json
import os

options = webdriver.ChromeOptions()
parser = argparse.ArgumentParser(
    description="A script to get stock and news info and calculate rise/fall."
)
parser.add_argument(
    "-showBrowser", action="store_true", help="Show browser if this flag is passed"
)

args = parser.parse_args()
show_browser = args.showBrowser
profile = profiles.Windows()
options = webdriver.ChromeOptions()
if not show_browser:
    options.add_argument("--headless=new")

driver = Chrome(
    profile,
    options=options,
    uc_driver=False,
)


def get_news():
    news = ""
    driver.get("https://news.google.com/topstories")
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "article"))
    )

    def scroll_down(repeat=3):
        body = driver.find_element(By.TAG_NAME, "body")
        for _ in range(repeat):
            body.send_keys(Keys.END)

    scroll_down(repeat=5)

    articles = driver.find_elements(By.CSS_SELECTOR, "article")

    for article in articles:
        try:
            title_elem = article.find_element(By.CSS_SELECTOR, "a.gPFEn")
            # source_elem = article.find_element(By.CSS_SELECTOR, "div.vr1PYe")
            # time_elem = article.find_element(By.CSS_SELECTOR, "time.hvbAAd")

            title = title_elem.text.strip()
            # link = title_elem.get_attribute("href")
            # source = source_elem.text.strip()
            # time_ago = time_elem.text.strip()

            news = news + f"{title}\n"
        except Exception:
            continue
    return news


def get_stock_info():
    stock_info = ""
    driver.get("https://www.cnn.com/markets")

    wait = WebDriverWait(driver, 15)
    wait.until(
        EC.presence_of_element_located((By.CSS_SELECTOR, ".basic-table__entry-1UF7dk"))
    )

    rows = driver.find_elements(By.CSS_SELECTOR, ".basic-table__entry-1UF7dk")

    for row in rows:
        try:
            ticker_el = row.find_elements(By.CSS_SELECTOR, ".ticker a")
            company_el = row.find_elements(By.CSS_SELECTOR, ".title-column span")
            price_el = row.find_elements(
                By.CSS_SELECTOR, ".basic-table__price-container-1xrkt9 span"
            )
            change_el = row.find_elements(
                By.CSS_SELECTOR, ".basic-table__change-1zbRwI span"
            )
            volume_el = row.find_elements(
                By.CSS_SELECTOR, ".basic-table__volume-3V90t3"
            )
            low52_el = row.find_elements(By.CSS_SELECTOR, ".low__text")
            high52_el = row.find_elements(By.CSS_SELECTOR, ".high__text")

            if not (
                ticker_el
                and company_el
                and price_el
                and change_el
                and volume_el
                and low52_el
                and high52_el
            ):
                continue

            ticker = ticker_el[0].text
            company = company_el[0].text
            price = price_el[0].text
            change = change_el[0].text
            percent = change_el[1].text if len(change_el) > 1 else ""
            volume = volume_el[0].text
            low52 = low52_el[0].text
            high52 = high52_el[0].text

            stock_info = (
                stock_info
                + f"{ticker}: {company}\nPrice: {price} | Change: {change} | % Change: {percent}\nVolume: {volume} | 52W Range: {low52} - {high52}"
            )
        except Exception:
            continue
    return stock_info


CONFIG_FILE = "config.json"


def load_or_create_config():
    # Check if the config file exists
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as file:
            try:
                config = json.load(file)
                # Ensure required keys exist
                if "username" in config and "password" in config:
                    return config["username"], base64.b64decode(
                        config["password"]
                    ).decode("utf-8")
                else:
                    print("Config file is missing required fields.")
            except json.JSONDecodeError:
                print("Error decoding JSON. Creating a new config.")
            except (base64.binascii.Error, UnicodeDecodeError) as e:
                # Print any errors that occur during decoding
                print("Error decoding password. Creating a new config.")
    # If file doesn't exist or is invalid, create a new one
    username = input("Enter your username: ")
    password = input("Enter your password: ")
    config = {
        "username": username,
        "password": base64.b64encode(password.encode("utf-8")).decode("utf-8"),
    }

    # Save to file
    with open(CONFIG_FILE, "w") as file:
        json.dump(config, file, indent=4)
    print("Config saved successfully.")
    return username, password


STORED_EMAIL_ID, STORED_EMAIL_PASS = load_or_create_config()


class ChatGPTAuthWallException(Exception):
    pass


def get_chatgpt_response(prompt):
    driver.get("https://chatgpt.com")

    n = 2
    RESPONSE_TIMEOUT = 60

    def wait_until_loaded():
        try:
            WebDriverWait(driver, 60).until(
                EC.presence_of_element_located((By.ID, "prompt-textarea"))
            )
        except:
            wait_until_loaded()

    def get_prompt_response(prompt):
        nonlocal n
        textarea = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "prompt-textarea"))
        )
        textarea.send_keys(prompt)
        button = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, "button[data-testid='send-button']")
            )
        )
        button.click()
        try:
            response = WebDriverWait(driver, RESPONSE_TIMEOUT).until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, f"article[data-testid='conversation-turn-{n}']")
                )
            )
            while len(response.text.split("\n")) <= 1:
                time.sleep(0.5)
            while driver.find_elements(By.CLASS_NAME, "streaming-animation"):
                time.sleep(0.25)
        except TimeoutException:
            n = n + 2
            return

        response = response.text
        if "You're giving feedback on a new version of ChatGPT." in response:
            response = response.replace(
                "You're giving feedback on a new version of ChatGPT.", ""
            )
            response = response.replace(
                "Which response do you prefer? Responses may take a moment to load.", ""
            )
            response = response.replace("Response 1", "")
            response = response.replace("Response 2", "")
            response = response.replace("Response 3", "")
            response = response.replace("I prefer this response", "")
        response = response.split("\n")
        del response[0]
        response = "{0}".format(".".join(response))
        n = n + 2
        return response

    wait_until_loaded()
    try:
        WebDriverWait(driver, 5).until(EC.url_contains("https://auth.openai.com"))
    except TimeoutException:
        pass

    try:
        if "https://auth.openai.com" in driver.current_url:
            # Click on "Continue with Google"
            google_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable(
                    (By.XPATH, "//button[.//span[text()='Continue with Google']]")
                )
            )
            google_button.click()

            # Switch to Google login page
            # Wait for the email input field and fill it
            email_input = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "identifierId"))
            )
            WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.ID, "identifierId"))
            )
            email_input.send_keys(STORED_EMAIL_ID)

            # Click "Next" after entering email
            next_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable(
                    (By.XPATH, "//span[text()='Next']/ancestor::button")
                )
            )
            next_button.click()

            # Wait for the password input field and fill it
            password_input = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.NAME, "Passwd"))
            )
            WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.NAME, "Passwd"))
            )
            password_input.send_keys(STORED_EMAIL_PASS)

            # Click "Next" after entering the password
            next_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable(
                    (By.XPATH, "//span[text()='Next']/ancestor::button")
                )
            )
            next_button.click()

            # Wait for the page to redirect back to ChatGPT
            WebDriverWait(driver, 10).until(EC.url_contains("https://chatgpt.com"))
    except TimeoutException:
        raise ChatGPTAuthWallException("Authentication failed.")
    return get_prompt_response(prompt)


import threading
import time
import sys


def print_progress(text: str, done_flag: threading.Event):
    def run():
        start_time = time.time()
        while not done_flag.is_set():
            elapsed = int(time.time() - start_time)
            sys.stdout.write(f"\r{text} - {elapsed}s")
            sys.stdout.flush()
            time.sleep(1)

    threading.Thread(target=run, daemon=True).start()


flag = threading.Event()
print_progress("Waiting for stock market info", flag)
stock_info = get_stock_info()
flag.set()
print(f"\rStock info: {stock_info}")

flag = threading.Event()
print_progress("Waiting for latest news", flag)
news = get_news()
flag.set()
print(f"\rNews: {news}")

prompt = f"Stock market: {stock_info}\n\nNews: {news}\n\nBased on the above information summarize the rise/fall percentages of stock market."
flag = threading.Event()
print_progress("Waiting for ChatGPT response", flag)
try:
    response = get_chatgpt_response(prompt)
except ChatGPTAuthWallException:
    flag.set()
    print(
        "\rError: Couldn't get a response from ChatGPT due to unsuccessful auth-wall bypass."
    )
    
    sys.exit(1)
flag.set()
print(f"\rResponse: {response}")
