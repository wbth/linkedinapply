
import os
import time
import logging
import random
import json
import pandas as pd
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from plyer import notification

# Setup logging
logging.basicConfig(filename='linkedin_activity.log', level=logging.INFO, format='%(asctime)s - %(message)s')

# Load and save settings
def load_settings():
    if os.path.exists('settings.json'):
        with open('settings.json', 'r') as file:
            return json.load(file)
    else:
        return {
            "username": "",
            "password": "",
            "keyword": "",
            "location": "",
            "easy_apply": True,
            "job_type": "remote",
            "applied_companies": []
        }

def save_settings(settings):
    with open('settings.json', 'w') as file:
        json.dump(settings, file, indent=4)

def get_random_user_agent():
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/101.0.4951.64 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.159 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/537.36 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1",
        "Mozilla/5.0 (iPad; CPU OS 14_0 like Mac OS X) AppleWebKit/537.36 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1"
    ]
    return random.choice(user_agents)

def setup_driver():
    chrome_options = Options()
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument("--disable-notifications")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument(f"user-agent={get_random_user_agent()}")
    # Optional: Enable headless mode for background execution
    # chrome_options.add_argument("--headless")
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=chrome_options)

# LinkedIn login
def login_linkedin(driver, username, password):
    try:
        driver.get("https://www.linkedin.com/login")
        wait = WebDriverWait(driver, 10)
        time.sleep(random.uniform(2, 4))  # Random delay
        wait.until(EC.presence_of_element_located((By.ID, "username"))).send_keys(username)
        time.sleep(random.uniform(1, 3))  # Random delay
        driver.find_element(By.ID, "password").send_keys(password)
        time.sleep(random.uniform(1, 3))  # Random delay
        
        # Uncheck "Remember Me" if it exists
        try:
            remember_me_checkbox = driver.find_element(By.XPATH, "//input[@id='remember-me']")
            if remember_me_checkbox.is_selected():
                remember_me_checkbox.click()
                logging.info("Unchecked 'Remember Me' option.")
        except Exception as e:
            logging.info(f"'Remember Me' option not found or could not be unchecked: {e}")
        
        driver.find_element(By.XPATH, "//button[@type='submit']").click()
        logging.info("Logged in to LinkedIn successfully.")
        print("Login successful!")
    except Exception as e:
        logging.error(f"Error during LinkedIn login: {e}")
        notification.notify(title="LinkedIn Script Error", message="Error during LinkedIn login")
        print("Error during LinkedIn login.")


# Job search and filtering
def search_jobs(driver, keyword, location, easy_apply, job_type):
    try:
        print("Starting job search...")
        logging.info("Starting job search on LinkedIn.")

        # Mapping job type to LinkedIn filter values
        work_type_mapping = {
            "hybrid": "3",
            "remote": "2",
            "onsite": "1"
        }
        
        work_type = work_type_mapping.get(job_type.lower(), "2")  # Default to "remote" if not recognized

        # Define geoId for Indonesia or other location-based geoIds
        geo_id_mapping = {
            "indonesia": "102478259",
            "worldwide": "92000000"
        }

        geo_id = geo_id_mapping.get(location.lower(), geo_id_mapping["indonesia"])  # Default to Indonesia's geoId

        # Construct the search URL
        easy_apply_flag = "true" if easy_apply else "false"
        url = (f"https://www.linkedin.com/jobs/search/?f_AL={easy_apply_flag}"
               f"&f_WT={work_type}&geoId={geo_id}&keywords={keyword}&refresh=true")
        
        driver.get(url)
        print(f"Searching for jobs with keyword '{keyword}' in '{location}', job type: {job_type}.")
        logging.info(f"Navigated to job search URL: {url}")

        wait = WebDriverWait(driver, 10)
        time.sleep(random.uniform(2, 4))  # Random delay to simulate human behavior

        # Collect job cards
        time.sleep(random.uniform(5, 10))  # Random delay to simulate loading
        job_cards = driver.find_elements(By.CLASS_NAME, "job-card-container")
        jobs = []

        # Collect up to the last 20 job cards
        for job in job_cards[:20]:
            job_title = job.text.split("\n")[0]
            company_name = job.text.split("\n")[1] if len(job.text.split("\n")) > 1 else "Unknown Company"
            jobs.append({"Job Title": job_title, "Company": company_name})

        return jobs

    except Exception as e:
        logging.error(f"Error during job search: {e}")
        print("Error during job search.")
        return []

    
# Function to apply to jobs and log activity
def apply_jobs(driver, use_existing_resume, pdf_path, settings):
    try:
        wait = WebDriverWait(driver, 10)
        job_cards = driver.find_elements(By.CLASS_NAME, "job-card-container")

        applied_jobs = []  # Collect applied job details

        for job in job_cards[:20]:  # Limit to the first 20 job cards to prevent overload
            try:
                job.click()  # Click on the job card to open details
                time.sleep(random.uniform(2, 4))  # Random delay to mimic human behavior

                job_title = job.text.split("\n")[0]
                company_name = job.text.split("\n")[1] if len(job.text.split("\n")) > 1 else "Unknown Company"
                print(f"\nJob: {job_title} at {company_name}")
                apply_now = input("Do you want to apply for this job? (y/n): ").strip().lower()

                if apply_now == 'y':
                    logging.info(f"Attempting to apply for job: {job_title} at {company_name}")

                    # Attempt to click the "Easy Apply" button
                    try:
                        easy_apply_button = wait.until(EC.element_to_be_clickable((By.CLASS_NAME, "jobs-apply-button")))
                        easy_apply_button.click()
                        logging.info("Clicked 'Easy Apply' button.")

                        # If not using an existing resume, upload a new one
                        if not use_existing_resume:
                            upload_button = wait.until(EC.presence_of_element_located((By.XPATH, "//input[@type='file']")))
                            upload_button.send_keys(pdf_path)  # Upload the resume
                            logging.info("Uploaded custom resume.")

                        # Submit the application
                        submit_button = wait.until(EC.element_to_be_clickable(
                            (By.XPATH, "//button[contains(@class, 'artdeco-button--primary')]")
                        ))
                        submit_button.click()
                        logging.info("Submitted the application.")
                        applied_jobs.append({"Job Title": job_title, "Company": company_name})

                        # Track the applied company in settings
                        settings["applied_companies"].append(company_name)

                        # Close the "Easy Apply" modal
                        close_button = wait.until(EC.element_to_be_clickable(
                            (By.CLASS_NAME, "artdeco-modal__dismiss")
                        ))
                        close_button.click()
                        logging.info("Closed the application modal.")

                    except Exception as e:
                        logging.warning(f"Could not complete Easy Apply for job: {job_title}. Reason: {e}")
                else:
                    logging.info(f"Skipped application for job: {job_title} at {company_name}")

            except Exception as e:
                logging.warning(f"Error accessing job card: {e}")

        if applied_jobs:
            print("\nSuccessfully applied to the following jobs:")
            for job in applied_jobs:
                print(f"- {job['Job Title']} at {job['Company']}")
                logging.info(f"Applied to: {job['Job Title']} at {job['Company']}")
        else:
            print("\nNo applications were successfully submitted.")

    except Exception as e:
        logging.error(f"Error during job application process: {e}")
        notification.notify(title="LinkedIn Script Error", message="Error during job application")
        print("Error during job application.")



# Main function
def main():
    settings = load_settings()
    
    # Login
    username = input("Enter your LinkedIn Username: ")
    password = input("Enter your LinkedIn Password: ")

    driver = setup_driver()
    login_linkedin(driver, username, password)

    # Search settings
    keyword = input("Enter job search keyword: ")
    location = input("Enter job location: ")
    easy_apply = input("Apply Easy Apply filter? (y/n): ").strip().lower() == 'y'
    job_type = input("Enter job type (remote/hybrid/onsite): ").strip().lower()

    # Search jobs
    jobs = search_jobs(driver, keyword, location, easy_apply, job_type)
    if jobs:
        print(f"\nTotal jobs found: {len(jobs)}")
        use_existing_resume = input("Use existing resume on LinkedIn? (y/n): ").strip().lower() == 'y'
        pdf_path = None

        if not use_existing_resume:
            pdf_path = input("Enter the path to your PDF resume: ").strip()
            if not os.path.exists(pdf_path):
                print("Invalid file path. Exiting.")
                driver.quit()
                return

        # Apply to jobs
        apply_jobs(driver, use_existing_resume, pdf_path, settings)
        save_settings(settings)

        # Show applied companies
        print("\nCompanies you have applied to:")
        for company in settings["applied_companies"]:
            print(f"- {company}")

    driver.quit()

if __name__ == "__main__":
    main()
