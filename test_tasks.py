from selenium import webdriver
from selenium.webdriver.common.by import By
import time

driver = webdriver.Chrome()

# Zaloguj się przed dodaniem zadania
driver.get("http://127.0.0.1:5000/login")
driver.find_element(By.NAME, "username").send_keys("testuser")
driver.find_element(By.NAME, "password").send_keys("testpassword")
driver.find_element(By.CLASS_NAME, "btn-primary").click()

time.sleep(2)  # Poczekaj na przekierowanie

# Dodaj nowe zadanie
driver.get("http://127.0.0.1:5000/homepage")
driver.find_element(By.ID, "title").send_keys("Nowe zadanie")
driver.find_element(By.ID, "description").send_keys("Opis zadania")
driver.find_element(By.CLASS_NAME, "btn-primary").click()

time.sleep(2)

# Sprawdź, czy zadanie pojawiło się na stronie
tasks = driver.find_element(By.ID, "recently-added").text
assert "Nowe zadanie" in tasks

driver.quit()
