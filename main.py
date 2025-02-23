import time
import random
import undetected_chromedriver as uc
import pandas as pd
import tkinter as tk
from tkinter import simpledialog
from selenium.webdriver.common.action_chains import ActionChains
from fake_useragent import UserAgent  # Random user-agent generator
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import os
import logging
import pickle  # For saving and loading cookies

# Dictionaries for user choices
categories_dict = {}
storage_data = {}
# the end list that will be rendered in the excel sheet
results_data = []

# GUI Class
import tkinter as tk
from tkinter import ttk
class ListSelectionApp:
    def __init__(self, root, items):
        self.root = root
        self.root.title("Select an Item")
        self.root.geometry("1200x800")  # Set window size
        self.set_dark_mode()
        self.selected_item = None
        self.buttons_frame = ttk.Frame(root)
        self.buttons_frame.grid(row=1, column=0, pady=20, padx=20, sticky="nsew")
        columns = 6
        row = 0
        column = 0
        self.buttons = []
        for item in items:
            button = tk.Button(self.buttons_frame, text=item, command=lambda i=item: self.on_button_click(i), bg="#4CAF50", fg="white", font=('Arial', 12))
            button.grid(row=row, column=column, pady=10, padx=10, sticky="ew")
            self.buttons.append(button)
            column += 1
            if column == columns:  
                column = 0
                row += 1
        for i in range(len(items)):
            self.buttons_frame.grid_columnconfigure(i, weight=1)
        self.buttons_frame.grid_rowconfigure(row, weight=1)
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
    def set_dark_mode(self):
        # تخصيص الألوان لوضع المظلم
        self.root.configure(bg="#121212") 
        ttk.Style().configure('TButton', background='#333333', foreground='#000000', font=('Arial', 12))
        ttk.Style().configure('TLabel', background='#121212', foreground='#000000', font=('Arial', 12))
    def on_button_click(self, item):
        self.selected_item = item
        logging.info(f"Selected item: {self.selected_item}")
        self.root.quit()
    def on_close(self):
        self.selected_item = None
        self.root.quit()

def showListAndReturnInput(dict):
    root = tk.Tk()
    items = list(dict.keys())
    app = ListSelectionApp(root, items)
    root.mainloop()
    root.destroy()
    return app.selected_item

# Simulate human
def humanBehavior(min = 30):
    time.sleep(min + random.uniform(0, 20))

# Extract Filters buttons data then store it in the specified container 
def extractFiltersData(link, storage_dict, container_class, item_xpath):
    try:
        driver.get(link)
        container = driver.find_element("class name", container_class)
        items = container.find_elements("xpath", item_xpath)
        for item in items:
            # Remove <span> elements if it exists using JavaScript
            driver.execute_script("var spans = arguments[0].querySelectorAll('span'); spans.forEach(s => s.remove());", item)
            element_href = item.get_attribute("href")
            element_text = item.get_attribute("innerText").strip()
            if element_text:
                storage_dict[element_text] = element_href
        return 1
    except NoSuchElementException:
        return -1 
    except Exception as e:
        logging.error(f"Error extracting data from {link}: {e}")

# Extract advisor phone number out of the card
def extractPhoneNumber(link):
    phoneNumber = '-'
    clientName = '-'  # New field for client's name
    driver.get(link)
    try:
        phoneElement = driver.find_element(By.CLASS_NAME, "_callText__upXJR")
        humanBehavior()
        phoneElement.click()

        # Wait for the text to change from "إتصال" to something else
        WebDriverWait(driver, 20).until(
            lambda d: phoneElement.text.strip() != "إتصال"
        )
        # Get the updated phone number using JavaScript
        phoneNumber = driver.execute_script("return arguments[0].innerText;", phoneElement).strip()
    except NoSuchElementException:
        logging.warning(f"No such element found for phone number on {link}")
    except Exception as e:
        logging.error(f"Error extracting phone number from {link}: {e}")
    
    # Extract client's name regardless of phone number extraction success
    try:
        clientNameElement = driver.find_element(By.CLASS_NAME, "_name__W6hBp")
        clientName = clientNameElement.get_attribute("innerText").strip()
    except NoSuchElementException:
        logging.warning(f"No such element found for client name on {link}")
    except Exception as e:
        logging.error(f"Error extracting client name from {link}: {e}")
    
    humanBehavior()
    driver.back()
    logging.info(f"Extracted phone number: {phoneNumber}, client name: {clientName}")
    return phoneNumber, clientName

# Extract cards data in the current page
def extractPageCards(link, pageNumber):
    allCardsLinks = []
    try:
        driver.get(f"{link}/{pageNumber}")
        logging.info(f"Navigating to {link}/{pageNumber}")
        wait = WebDriverWait(driver, 20)
        container = wait.until(EC.presence_of_element_located((By.CLASS_NAME, "_list__Ka30R")))
        
        allChildrenCards = container.find_elements("xpath", "./div")
        # No more cards
        if not allChildrenCards:
            logging.info("Entered No cards condition")
            return -1
        for card in allChildrenCards:
            cardDetails = {
                "اسم العميل": "-" ,
                "العنوان": "-",
                "الوصف": "-",
                "المساحة": "-",
                "عدد الغرف": "-",
                "عدد الصالات": "-",
                "عدد الحمامات": "-",
                "السعر": "-",
                "الجوال": "-",
                "لينك المعاينة": "-"
            }
            try:
                title = card.find_element("xpath", ".//h4").get_attribute("innerText").strip()
                cardDetails["العنوان"] = title
            except NoSuchElementException:
                pass
            try:
                price = card.find_element("class name", "_price__X51mi").get_attribute("innerText").strip()
                cardDetails["السعر"] = price
            except NoSuchElementException:
                pass
            try:
                description = card.find_element("class name", "_description__zVaD6").get_attribute("innerText").strip()
                cardDetails["الوصف"] = description
            except NoSuchElementException:
                pass
            try:
                cardLink = card.find_element("xpath", "./a").get_attribute("href")
                cardDetails["لينك المعاينة"] = cardLink
                allCardsLinks.append(cardLink)
            except NoSuchElementException:
                pass
            try:
                area = card.find_element("xpath", ".//img[@alt='المساحة']/ancestor::div[1]").text.strip()
                cardDetails["المساحة"] = area
            except:
                pass
            try:
                rooms = card.find_element("xpath", ".//img[@alt='عدد الغرف']/ancestor::div[1]").text.strip()
                cardDetails["عدد الغرف"] = rooms
            except:
                pass
            try:
                halls = card.find_element("xpath", ".//img[@alt='عدد الصالات']/ancestor::div[1]").text.strip()
                cardDetails["عدد الصالات"] = halls
            except:
                pass
            try:
                bath = card.find_element("xpath", ".//img[@alt='عدد الحمامات']/ancestor::div[1]").text.strip()
                cardDetails["عدد الحمامات"] = bath
            except:
                pass             
            results_data.append(cardDetails)
            
        j = 0
        for i in range((pageNumber - 1) * len(allChildrenCards), len(results_data)):
            humanBehavior()
            phoneNumber, clientName = extractPhoneNumber(allCardsLinks[j])
            results_data[i]["الجوال"] = phoneNumber
            results_data[i]["اسم العميل"] = clientName
            j += 1
    except NoSuchElementException as e:
        logging.error(f"No such element found extract page cards: {e}")
        return -1
    except Exception as e:
        logging.error(f"Error extracting page cards from {link}: {e}")

# Set up Chrome options
options = uc.ChromeOptions()
options.add_argument("--disable-blink-features=AutomationControlled")  # Bypass bot detection
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
# Start the browser
driver = uc.Chrome(options=options)

# Define the path to store cookies in AppData
appdata_path = os.getenv('APPDATA')
cookies_file = os.path.join(appdata_path, "realestate_cookies.pkl")

# Load cookies if available
if os.path.exists(cookies_file):
    driver.get("https://sa.aqar.fm")
    with open(cookies_file, "rb") as f:
        cookies = pickle.load(f)
        for cookie in cookies:
            driver.add_cookie(cookie)
    driver.refresh()

def main():
    driver.get("https://sa.aqar.fm/login")
    humanBehavior(100)
    extractFiltersData("https://sa.aqar.fm/", categories_dict, "_list__A_7Gb", "./a")
    if __name__ == "__main__":
        userInput = showListAndReturnInput(categories_dict)
    selectedLink = categories_dict[userInput]
    while extractFiltersData(selectedLink, storage_data, "_bottom__L7b67", ".//a") != -1:
        if __name__ == "__main__":
            userInput = showListAndReturnInput(storage_data)
        selectedLink = storage_data[userInput]
        storage_data.clear()
    logging.info("Success")
    logging.info(selectedLink)
    pageNumber = 1  # Start from page 1
    while True:
        humanBehavior()
        if extractPageCards(selectedLink, pageNumber) == -1:
            break
        pageNumber += 1
    logging.info(f"Total results: {len(results_data)}")
    
    # Save cookies before closing the browser
    with open(cookies_file, "wb") as f:
        pickle.dump(driver.get_cookies(), f)
    
    # Close the browser
    driver.quit()
    # Save to Excel file
    df = pd.DataFrame(results_data)
    file_name = "output.xlsx"
    df.to_excel(file_name, index=False, engine="openpyxl")
    os.startfile(file_name)
# Launch the script
main()