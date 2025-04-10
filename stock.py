from selenium_profiles.webdriver import Chrome
from selenium_profiles.profiles import profiles
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium import webdriver
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
        except Exception as e:
            continue
    return stock_info


print(get_stock_info())
