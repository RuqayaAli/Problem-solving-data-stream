from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import pandas as pd
import time

options = webdriver.ChromeOptions()
options.add_argument('--headless') 
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')

service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=options)

url = "https://books.toscrape.com/"
driver.get(url)
time.sleep(2)  

books = driver.find_elements(By.CSS_SELECTOR, "article.product_pod")

book_data = []

for book in books:
    title = book.find_element(By.TAG_NAME, "h3").find_element(By.TAG_NAME, "a").get_attribute("title")
    price = book.find_element(By.CLASS_NAME, "price_color").text
    availability = book.find_element(By.CLASS_NAME, "availability").text.strip()
    star_element = book.find_element(By.CSS_SELECTOR, "p.star-rating")
    star_rating = star_element.get_attribute("class").replace("star-rating", "").strip()

    book_data.append({
        "Title": title,
        "Price": price,
        "Availability": availability,
        "Star Rating": star_rating
    })

driver.quit()

df = pd.DataFrame(book_data)
df.to_csv("books_page1.csv", index=False)

print(" Data saved to books_page1.csv")
