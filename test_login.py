from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import  Keys
import time


driver = webdriver.Chrome()



driver.get("http://127.0.0.1:5000/register")


driver.find_element(By.NAME, "username").send_keys("newuser2")
driver.find_element(By.NAME, "password").send_keys("securepassword")
driver.find_element(By.CLASS_NAME, "btn-primary").click()


time.sleep(2)


assert "Sign In" in driver.title



driver.get("http://127.0.0.1:5000/login")


username_input = driver.find_element(By.NAME, "username")
username_input.send_keys("newuser2")


password_input = driver.find_element(By.NAME, "password")
password_input.send_keys("securepassword")


submit_button = driver.find_element(By.CLASS_NAME, "btn-primary")
submit_button.click()

time.sleep(2)


assert "Task Organizer" in driver.title


driver.get("http://127.0.0.1:5000/homepage")
driver.find_element(By.ID, "title").send_keys("Nowe zadanie")
driver.find_element(By.ID, "description").send_keys("Opis zadania")
driver.find_element(By.CLASS_NAME, "btn-primary").click()

time.sleep(2)

tasks = driver.find_element(By.ID, "recently-added").text
assert "Nowe zadanie" in tasks



driver.quit()