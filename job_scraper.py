import os
import csv
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import time

# --- CONFIGURATION ---

JOB_KEYWORDS = [
    'Multimedia Producer', 'Producer', 'Video Producer', 'Content Creator', 'Editor', 'Graphic Designer',
    'Art Director', 'Creative Director', 'Video Editing', 'Webinar Production', 'Podcast Editing', 'Event Planning'
]

JOB_BOARDS = {
    'Indeed': 'https://www.indeed.com/jobs?q={keyword}&l=remote',
    'WeWorkRemotely': 'https://weworkremotely.com/remote-jobs/search?term={keyword}'
}

CSV_FILE_NAME = 'job_listings.csv'
EMAIL_SENDER = os.environ['EMAIL_SENDER']
EMAIL_RECEIVER = os.environ['EMAIL_SENDER']
EMAIL_PASSWORD = os.environ['EMAIL_PASSWORD']

# --- SELENIUM SETUP ---

chrome_options = Options()
chrome_options.add_argument('--headless')
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')
driver = webdriver.Chrome(options=chrome_options)

def scrape_jobs():
    jobs = []
    for keyword in JOB_KEYWORDS:
        for board_name, url_template in JOB_BOARDS.items():
            url = url_template.format(keyword=keyword.replace(' ', '+'))
            driver.get(url)
            time.sleep(3)  # Wait for the page to load

            if board_name == 'Indeed':
                jobs += parse_indeed(driver, keyword, board_name)
            elif board_name == 'WeWorkRemotely':
                jobs += parse_weworkremotely(driver, keyword, board_name)

    return jobs

def parse_indeed(driver, keyword, board):
    jobs = []
    job_cards = driver.find_elements(By.CLASS_NAME, 'job_seen_beacon')

    for card in job_cards:
        title = card.find_element(By.TAG_NAME, 'h2').text if card.find_elements(By.TAG_NAME, 'h2') else 'Unknown'
        company = card.find_element(By.CLASS_NAME, 'companyName').text if card.find_elements(By.CLASS_NAME, 'companyName') else 'Unknown'
        location = card.find_element(By.CLASS_NAME, 'companyLocation').text if card.find_elements(By.CLASS_NAME, 'companyLocation') else 'Unknown'

        job = {
            'Organization': company,
            'Job Title': title,
            'Sector': keyword,
            'Job type': 'Unknown',
            'Applied?': 'No',
            'Location': location,
            'On-site?': 'Unknown',
            'Job board': board,
            'Core job responsibilities': 'TBD'
        }
        jobs.append(job)
    return jobs

def parse_weworkremotely(driver, keyword, board):
    jobs = []
    sections = driver.find_elements(By.CLASS_NAME, 'jobs')

    for section in sections:
        features = section.find_elements(By.CLASS_NAME, 'feature')
        for job_post in features:
            title = job_post.find_element(By.CLASS_NAME, 'title').text if job_post.find_elements(By.CLASS_NAME, 'title') else 'Unknown'
            company = job_post.find_element(By.CLASS_NAME, 'company').text if job_post.find_elements(By.CLASS_NAME, 'company') else 'Unknown'

            job = {
                'Organization': company,
                'Job Title': title,
                'Sector': keyword,
                'Job type': 'Unknown',
                'Applied?': 'No',
                'Location': 'Remote',
                'On-site?': 'No',
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
    driver.quit()
