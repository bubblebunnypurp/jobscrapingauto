# job_scraper.py

import os
import requests
from bs4 import BeautifulSoup
import csv
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime

# --- CONFIGURATION ---

JOB_KEYWORDS = [
    'Multimedia Producer', 'Producer', 'Video Producer', 'Content Creator', 'Editor', 'Graphic Designer',
    'Art Director', 'Creative Director', 'Video Editing', 'Webinar Production', 'Podcast Editing', 'Event Planning'
]

INDUSTRIES = ['Healthcare', 'Education', 'Finance', 'Marketing', 'Film', 'Television']
JOB_BOARDS = ['https://www.indeed.com/jobs?q={keyword}&l=remote']  # Example job board
CSV_FILE_NAME = 'job_listings.csv'

EMAIL_SENDER = os.environ['EMAIL_SENDER']
EMAIL_RECEIVER = os.environ['EMAIL_SENDER']  # sending to self
EMAIL_PASSWORD = os.environ['EMAIL_PASSWORD']


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


def save_to_csv(jobs):
    headers = ['Organization', 'Job Title', 'Sector', 'Job type', 'Applied?', 'Location', 'On-site?', 'Job board', 'Core job responsibilities']
    with open(CSV_FILE_NAME, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=headers)
        writer.writeheader()
        for job in jobs:
            writer.writerow(job)


def send_email_with_csv():
    subject = f"Job Scraper Results - {datetime.now().strftime('%Y-%m-%d')}"
    body = "Attached is the latest list of job opportunities."

    msg = MIMEMultipart()
    msg['From'] = EMAIL_SENDER
    msg['To'] = EMAIL_RECEIVER
    msg['Subject'] = subject

    msg.attach(MIMEText(body, 'plain'))

    with open(CSV_FILE_NAME, 'rb') as attachment:
        part = MIMEBase('application', 'octet-stream')
        part.set_payload(attachment.read())

    encoders.encode_base64(part)
    part.add_header('Content-Disposition', f'attachment; filename= {CSV_FILE_NAME}')

    msg.attach(part)

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
        server.login(EMAIL_SENDER, EMAIL_PASSWORD)
        server.send_message(msg)


if __name__ == '__main__':
    jobs = scrape_jobs()
    save_to_csv(jobs)
    send_email_with_csv()
    print(f"{len(jobs)} jobs scraped and CSV emailed.")
