from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import time
from datetime import datetime, timedelta
import re
from bs4 import BeautifulSoup
import requests
import csv
import json

"""
Scrapes Weather Data in Chicago with Selenium from NBC

Variables:
temp -- int: current temperature
feels -- int: feels like temperature
forecast_day -- dictionary
    key: number of days from today
    value: list [str: date, int: daily high, int: daily low, int: percipitation chance, str: weather condition, str: weather icon url]
forecast_hour --dictionary
    key: hour of day string
    value: list [int: temperature, int: precipitation %]
"""

forecast_day = {
    i: [(datetime.now() + timedelta(days = i)).strftime("%B %d, %Y")]
    for i in range(5)
}

options = Options()
options.add_argument("--headless")
url_nbc = "https://www.nbcchicago.com/weather/"
driver = webdriver.Chrome(options = options)
driver.get(url_nbc)
time.sleep(5)

temp = int(driver.find_element(By.CSS_SELECTOR, "span[class*='currentCond__temp--current'").text[:-1])

feels = int(driver.find_element(By.CSS_SELECTOR, "span[class*='currentCond__detail-value']").text[:-1])

high_low = driver.find_elements(By.CSS_SELECTOR, "span[class*='tenDay__temp']")[:10]
for i, val in enumerate(high_low):
    val = int(re.sub(r"[^0-9]", "", val.get_attribute("innerText").strip()))
    forecast_day[i // 2].append(val)

precip = driver.find_elements(By.CSS_SELECTOR, "div.tenDay__precip")[:5]
for i, val in enumerate(precip):
    val = int(re.sub(r"[^0-9]", "", val.get_attribute("innerText").strip()))
    forecast_day[i].append(val)

condition = driver.find_elements(By.CSS_SELECTOR, "span[class*='tenDay__sky-text']")[:5]
for i, val in enumerate(condition):
    val = val.get_attribute("innerText").strip()
    forecast_day[i].append(val)

condition_desc = driver.find_elements(By.CSS_SELECTOR, "div.tenDay__sky")[:5]
for i, val in enumerate(condition_desc):
    icon = val.find_element(By.TAG_NAME, "i")
    url = icon.value_of_css_property("background-image")[5:-2]
    forecast_day[i].append(url)

forecast_hour = {}
hours = driver.find_elements(By.CSS_SELECTOR, "div.hourlyForecast__hour") [:24]
for hour in hours:
    time_text = hour.find_element(By.CSS_SELECTOR, "div.hour__time").get_attribute("innerHTML")
    hour_precip = re.sub(r"[^0-9]", "", hour.find_element(By.CSS_SELECTOR, "div.hour__precip").get_attribute("innerHTML"))
    hour_temp = hour.find_element(By.CSS_SELECTOR, "span[class*='hour__temp'").get_attribute("innerHTML")
    forecast_hour[time_text] = [int(hour_temp[:-1]), int(hour_precip)]


"""
Scrape Weather Data with BeautifulSoup from Weather Underground

Variables:
wind -- int: wind speed in mph
aqi -- int: air quality index
humidity -- int: humidity in percent
yesterday -- str: comparison of today's weather with yesterday
"""

url_wu_1 = "https://www.wunderground.com/health/us/il/chicago?cm_ven=localwx_modaq"
response = requests.get(url_wu_1)
soup = BeautifulSoup(response.text, "html.parser")

info_row = soup.find("div", class_ = "row feels-like-values").find_all("div", class_ = "columns small-12")
wind = int(info_row[1].find("span", class_ = "actual").text[:-3].strip())
aqi = int(soup.find("div", class_ = "aqi-value").text)
humidity = int(info_row[0].find_all("span", class_ = "actual")[1].text[:-1])

url_wu2 = "https://www.wunderground.com/weather/us/il/chicago"
response = requests.get(url_wu2)
soup = BeautifulSoup(response.text, "html.parser")

yesterday = soup.find("p", class_ = "weather-quickie").find("span").text

with open("projects/project-one/data/p1_variables.csv", "w", newline = "") as f:
    writer = csv.writer(f)
    writer.writerow(["temperature", "feels like", "wind speed", "air quality index", "humidity", "yesterday description"])
    writer.writerow([temp, feels, wind, aqi, humidity, yesterday])

with open("projects/project-one/data/p1_forecast_day.csv", "w", newline = "") as f:
    writer = csv.writer(f)
    writer.writerow(["days from today", "date", "daily high", "daily low", "precip day", "condition", "condition icon"])
    for key, values in forecast_day.items():
        writer.writerow([key] + values)

with open("projects/project-one/data/p1_forecast_hour.csv", "w", newline = "") as f:
    writer = csv.writer(f)
    writer.writerow(["hour", "temperature", "precip hour"])
    for key, values in forecast_hour.items():
        writer.writerow([key] + values)

