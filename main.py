import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from time import sleep

from dotenv import load_dotenv
import requests
from bs4 import BeautifulSoup
from rich import print
from selenium import webdriver
from selenium.webdriver.common.by import By


load_dotenv(dotenv_path='dot.env')


def check_availability(driver, campground_url, date):
    driver.get(campground_url)

    soup = BeautifulSoup(driver.page_source, "html.parser")
    shortform_date = (
        f"{date.split(' ')[1][:3]} {date.split(' ')[2].removesuffix(',')}".strip()
    )
    while not (
        statuses := [
            date["aria-label"]
            for date in soup.find_all("button")
            if date.attrs.keys().__contains__("aria-label")
        ]
    ).__contains__(date):
        button = driver.find_element(By.CLASS_NAME, "forward")
        button.click()
        soup = BeautifulSoup(driver.page_source, "html.parser")

    return [
        rec
        for rec in statuses
        if rec.__contains__(shortform_date) & rec.__contains__("available")
    ]


def smtp_conn():
    smtp_server = smtplib.SMTP_SSL("smtp.gmail.com", 465)
    smtp_server.ehlo()

    gmail_user = os.environ.get("GMAIL_USER")
    gmail_app_password = os.environ.get("GMAIL_APP_PASSWORD")
    smtp_server.login(gmail_user, gmail_app_password)
    return smtp_server


def send_email_alert(message):
    smtp_server = smtp_conn()
    msg = MIMEMultipart()
    msg["From"] = os.environ.get("GMAIL_USER")
    msg["To"] = os.environ.get("EMAIL_RECIPIENT")
    msg[
        "Subject"
    ] = "A campsite is available! Now, git a goin ya carrot-chewin’ coyote!!"
    msg.attach(MIMEText(message, "plain"))

    try:
        smtp_server.send_message(msg)
        smtp_server.close()
        print("Email sent!")
    except Exception as e:
        print(f"[red]Error:\n\n{e}\n\n[/red]")


if __name__ == "__main__":
    retry_delay_in_minutes = 5
    while True:
        available_recs = check_availability(
            driver=webdriver.Chrome(),
            campground_url="https://www.recreation.gov/camping/campgrounds/233098", # Maumelle
            # campground_url="https://www.recreation.gov/camping/campgrounds/232447", # Yosemite
            date="Monday July 17, 2023",
        )
        if len(available_recs) > 0:
            print(f"[green]Availability found![/green]\n\n{available_recs}\n\n")
            print("Sending email alert...")
            send_email_alert(str(available_recs))
            break
        else:
            print(f"No availability yet. Checking again in {retry_delay_in_minutes} minutes...")
            sleep(retry_delay_in_minutes * 60)
        break
