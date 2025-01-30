from selenium import webdriver
from selenium.webdriver.common.by import By
import time


def register_user(driver, username, password):
    driver.get("http://127.0.0.1:5000/register")
    driver.find_element(By.NAME, "username").send_keys(username)
    driver.find_element(By.NAME, "password").send_keys(password)
    driver.find_element(By.CLASS_NAME, "btn-primary").click()
    time.sleep(2)
    assert "Sign In" in driver.title


def login_user(driver, username, password):
    driver.get("http://127.0.0.1:5000/login")
    driver.find_element(By.NAME, "username").send_keys(username)
    driver.find_element(By.NAME, "password").send_keys(password)
    driver.find_element(By.CLASS_NAME, "btn-primary").click()
    time.sleep(2)
    assert "Task Organizer" in driver.title


def add_task(driver, title, description):
    driver.get("http://127.0.0.1:5000/homepage")
    driver.find_element(By.ID, "title").send_keys(title)
    driver.find_element(By.ID, "description").send_keys(description)
    driver.find_element(By.CLASS_NAME, "btn-primary").click()
    time.sleep(2)

    tasks = driver.find_element(By.ID, "recently-added").text
    assert title in tasks


def logout_user(driver):
    driver.get("http://127.0.0.1:5000/logout")
    time.sleep(2)
    assert "Sign In" in driver.title


def verify_tasks(driver, expected_task):
    driver.get("http://127.0.0.1:5000/homepage")
    time.sleep(2)
    tasks = driver.find_element(By.ID, "recently-added").text
    assert expected_task in tasks


driver = webdriver.Chrome()


register_user(driver, "user1", "password1")
login_user(driver, "user1", "password1")


add_task(driver, "Zadanie user1", "Opis zadania user1")


logout_user(driver)

register_user(driver, "user2", "password2")
login_user(driver, "user2", "password2")


add_task(driver, "Zadanie user2", "Opis zadania user2")

logout_user(driver)


login_user(driver, "user1", "password1")
verify_tasks(driver, "Zadanie user1")
logout_user(driver)


login_user(driver, "user2", "password2")
verify_tasks(driver, "Zadanie user2")
logout_user(driver)


driver.quit()
