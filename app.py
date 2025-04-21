import asyncio
from quart import Quart, render_template
from concurrent.futures import ThreadPoolExecutor

from selenium_profiles.webdriver import Chrome
from selenium_profiles.profiles import profiles
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium import webdriver

import time
import json
import os
import base64

# Initialize app and executor
app = Quart(__name__)
executor = ThreadPoolExecutor()

# Init driver once
profile = profiles.Windows()
options = webdriver.ChromeOptions()
options.add_argument("--headless=new")
driver = Chrome(profile, options=options, uc_driver=True)

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
            except (base64.binascii.Error, UnicodeDecodeError):
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


def get_news():
    news = ""
    driver.get("https://news.google.com/topstories")
    WebDriverWait(driver, 15).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "article"))
    )
    body = driver.find_element(By.TAG_NAME, "body")
    for _ in range(5):
        body.send_keys(Keys.END)
        time.sleep(0.5)
    articles = driver.find_elements(By.CSS_SELECTOR, "article")
    for article in articles:
        try:
            title_elem = article.find_element(By.CSS_SELECTOR, "a.gPFEn")
            news += f"{title_elem.text.strip()}\n"
        except:
            continue
    return news.strip()


def get_stock_info():
    stock_info = ""
    driver.get("https://www.cnn.com/markets")
    WebDriverWait(driver, 15).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, ".basic-table__entry-1UF7dk"))
    )
    rows = driver.find_elements(By.CSS_SELECTOR, ".basic-table__entry-1UF7dk")
    for row in rows:
        try:
            ticker = row.find_element(By.CSS_SELECTOR, ".ticker a").text
            company = row.find_element(By.CSS_SELECTOR, ".title-column span").text
            price = row.find_element(
                By.CSS_SELECTOR, ".basic-table__price-container-1xrkt9 span"
            ).text
            change_els = row.find_elements(
                By.CSS_SELECTOR, ".basic-table__change-1zbRwI span"
            )
            change = change_els[0].text
            percent = change_els[1].text if len(change_els) > 1 else ""
            volume = row.find_element(
                By.CSS_SELECTOR, ".basic-table__volume-3V90t3"
            ).text
            low52 = row.find_element(By.CSS_SELECTOR, ".low__text").text
            high52 = row.find_element(By.CSS_SELECTOR, ".high__text").text

            stock_info += f"{ticker}: {company} | Price: {price} | Change: {change} | %: {percent} | Volume: {volume} | 52W: {low52}-{high52}\n"
        except:
            continue
    return stock_info.strip()


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
            email_input = WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.ID, "identifierId"))
            )
            WebDriverWait(driver, 20).until(
                EC.element_to_be_clickable((By.ID, "identifierId"))
            )
            email_input.send_keys(STORED_EMAIL_ID)

            # Click "Next" after entering email
            next_button = WebDriverWait(driver, 20).until(
                EC.element_to_be_clickable(
                    (By.XPATH, "//span[text()='Next']/ancestor::button")
                )
            )
            next_button.click()

            # Wait for the password input field and fill it
            password_input = WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.NAME, "Passwd"))
            )
            WebDriverWait(driver, 20).until(
                EC.element_to_be_clickable((By.NAME, "Passwd"))
            )
            password_input.send_keys(STORED_EMAIL_PASS)

            # Click "Next" after entering the password
            next_button = WebDriverWait(driver, 20).until(
                EC.element_to_be_clickable(
                    (By.XPATH, "//span[text()='Next']/ancestor::button")
                )
            )
            next_button.click()

            # Wait for the page to redirect back to ChatGPT
            WebDriverWait(driver, 20).until(EC.url_contains("https://chatgpt.com"))
    except TimeoutException as e:
        import traceback

        def get_traceback(error):
            etype = type(error)
            trace = error.__traceback__
            lines = traceback.format_exception(etype, error, trace)
            traceback_text = "".join(lines)
            return traceback_text

        traceback_text = get_traceback(e)
        print(f"Error: {traceback_text}")
        raise ChatGPTAuthWallException("Authentication failed.")
    return get_prompt_response(prompt)


# Async wrappers
async def run_blocking(func, *args):
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(executor, lambda: func(*args))


@app.route("/")
async def index():
    return await render_template("index.html")


@app.route("/api/news")
async def news_endpoint():
    return await run_blocking(get_news)


@app.route("/api/market")
async def stocks_endpoint():
    return await run_blocking(get_stock_info)


@app.route("/api/ai")
async def summary_endpoint():
    stock_info = await run_blocking(get_stock_info)
    news = await run_blocking(get_news)
    if not stock_info or not news:
        return "No data available", 500
    prompt = f"Stock market: {stock_info}\n\nNews: {news}\n\nSummarize rise/fall."
    response: str = await run_blocking(get_chatgpt_response, prompt)
    return response.replace(".", ".\n")


if __name__ == "__main__":
    app.run(port=80)
