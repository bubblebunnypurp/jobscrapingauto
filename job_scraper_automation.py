# job_scraper.py

import os
import json
import requests
from bs4 import BeautifulSoup
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import smtplib
from email.mime.text import MIMEText
from datetime import datetime

# --- CONFIGURATION ---

JOB_KEYWORDS = [
    'Multimedia Producer', 'Producer', 'Video Producer', 'Content Creator', 'Editor', 'Graphic Designer',
    'Art Director', 'Creative Director', 'Video Editing', 'Webinar Production', 'Podcast Editing', 'Event Planning'
]

INDUSTRIES = ['Healthcare', 'Education', 'Finance', 'Marketing', 'Film', 'Television']
MIN_SALARY = 65000
JOB_BOARDS = ['https://www.indeed.com/jobs?q={keyword}&l=remote']  # Example for demonstration
GOOGLE_SHEET_NAME = 'Job Tracker'

EMAIL_SENDER = os.environ['EMAIL_SENDER']
EMAIL_RECEIVER = os.environ['EMAIL_SENDER']  # sending to self
EMAIL_PASSWORD = os.environ['EMAIL_PASSWORD']

# --- AUTHENTICATE GOOGLE SHEETS ---
scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
credentials_info = json.loads(os.environ['GOOGLE_CREDENTIALS_JSON'])
creds = ServiceAccountCredentials.from_json_keyfile_dict(credentials_info, scope)
client = gspread.authorize(creds)

def scrape_jobs():
    jobs = []
    for keyword in JOB_KEYWORDS:
        for board in JOB_BOARDS:
            url = board.format(keyword=keyword.replace(' ', '+'))
            response = requests.get(url)
            soup = BeautifulSoup(response.text, 'html.parser')

            for job_card in soup.find_all('div', class_='job_seen_beacon'):
                title = job_card.find('h2')
                company = job_card.find('span', class_='companyName')
                location = job_card.find('div', class_='companyLocation')

                job = {
                    'Organization': company.text.strip() if company else 'Unknown',
                    'Job Title': title.text.strip() if title else 'Unknown',
                    'Sector': keyword,
                    'Job type': 'Unknown',
                    'Applied?': 'No',
                    'Location': location.text.strip() if location else 'Unknown',
                    'On-site?': 'Unknown',
                    'Job board': board,
                    'Core job responsibilities': 'TBD'
                }

                jobs.append(job)
    return jobs

def update_google_sheet(jobs):
    sheet = client.open(GOOGLE_SHEET_NAME).sheet1
    headers = ['Organization', 'Job Title', 'Sector', 'Job type', 'Applied?', 'Location', 'On-site?', 'Job board', 'Core job responsibilities']
    sheet.clear()
    sheet.append_row(headers)

    for job in jobs:
        row = [job[h] for h in headers]
        sheet.append_row(row)

def send_summary_email(jobs):
    subject = f"Job Scraper Summary - {datetime.now().strftime('%Y-%m-%d')}"
    body = f"{len(jobs)} new jobs have been added to your Job Tracker sheet."

    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = EMAIL_SENDER
    msg['To'] = EMAIL_RECEIVER

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
        server.login(EMAIL_SENDER, EMAIL_PASSWORD)
        server.send_message(msg)

if __name__ == '__main__':
    jobs = scrape_jobs()
    update_google_sheet(jobs)
    send_summary_email(jobs)
    print(f"{len(jobs)} jobs scraped and updated.")
