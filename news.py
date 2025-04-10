from selenium_profiles.webdriver import Chrome
from selenium_profiles.profiles import profiles
from selenium.webdriver.common.by import By
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import argparse

options = webdriver.ChromeOptions()
parser = argparse.ArgumentParser(
    description="A script to scrape CNN stock markets using selenium hidden with selenium profiles."
)
parser.add_argument(
    "-showBrowser", action="store_true", help="Show browser if this flag is passed"
)

args = parser.parse_args()
show_browser = args.showBrowser
profile = profiles.Windows()
options = webdriver.ChromeOptions()
if show_browser:
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
            source_elem = article.find_element(By.CSS_SELECTOR, "div.vr1PYe")
            time_elem = article.find_element(By.CSS_SELECTOR, "time.hvbAAd")

            title = title_elem.text.strip()
            # link = title_elem.get_attribute("href")
            # source = source_elem.text.strip()
            # time_ago = time_elem.text.strip()

            news = news + f"{title}\n"
        except Exception:
            continue
    return news


print(get_news())
