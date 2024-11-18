
import os
import time
import logging
import random
import json
from datetime import datetime
from geopy.geocoders import Nominatim  # Import geopy for Geo IP
from selenium import webdriver
from selenium.webdriver.common.by import By
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
            "applied_companies": []  # Ensure 'applied_companies' is initialized
        }

def save_settings(settings):
    with open('settings.json', 'w') as file:
        json.dump(settings, file, indent=4)

#def get_random_user_agent():
#    user_agents = [
#        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/101.0.4951.64 Safari/537.36",
#        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.159 Safari/537.36",
#        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
#        "Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/537.36 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1",
#        "Mozilla/5.0 (iPad; CPU OS 14_0 like Mac OS X) AppleWebKit/537.36 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1"
#    ]
#    return random.choice(user_agents)

def setup_driver():
    chrome_options = Options()
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument("--disable-notifications")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-gpu")
#    chrome_options.add_argument(f"user-agent={get_random_user_agent()}")
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=chrome_options)

# Function to get Geo IP location and Geo ID
def get_geo_ip(location_name):
    geo_id_mapping = {
        "indonesia": "102478259",
        "worldwide": "92000000",
        "united states": "103644278",
        "canada": "101174742",
        "united kingdom": "101165590",
        "australia": "101452733",
        "germany": "101282230",
        "france": "101292050",
        "india": "102713980",
        "malaysia": "101218837"  # Example Geo ID for Malaysia
    }
    location_name = location_name.lower()
    
    if location_name in geo_id_mapping:
        return geo_id_mapping[location_name]
    else:
        # Use geopy to attempt to resolve the location
        try:
            geolocator = Nominatim(user_agent="geoapiExercises")
            location = geolocator.geocode(location_name)
            if location:
                print(f"Detected location: {location.address}")
                # Default Geo ID if not found in mapping
                return geo_id_mapping.get("worldwide")
        except Exception as e:
            logging.error(f"Error getting Geo IP location: {e}")
    
    # Fallback Geo ID
    return geo_id_mapping.get("worldwide")

# LinkedIn login
def login_linkedin(driver, username, password):
    try:
        driver.get("https://www.linkedin.com/login")
        wait = WebDriverWait(driver, 10)
        time.sleep(random.uniform(2, 4))
        wait.until(EC.presence_of_element_located((By.ID, "username"))).send_keys(username)
        time.sleep(random.uniform(1, 3))
        driver.find_element(By.ID, "password").send_keys(password)
        time.sleep(random.uniform(1, 3))
        
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
        
        work_type = work_type_mapping.get(job_type.lower(), "2")
        geo_id = get_geo_ip(location)  # Get Geo ID using function

        # Construct the search URL
        easy_apply_flag = "true" if easy_apply else "false"
        url = (f"https://www.linkedin.com/jobs/search/?f_AL={easy_apply_flag}"
               f"&f_WT={work_type}&geoId={geo_id}&keywords={keyword}&refresh=true")
        
        driver.get(url)
        print(f"Searching for jobs with keyword '{keyword}' in '{location}', job type: {job_type}.")
        logging.info(f"Navigated to job search URL: {url}")

        wait = WebDriverWait(driver, 10)
        time.sleep(random.uniform(2, 4))

        # Minta jumlah roles dari pengguna
        roles_to_display = input("Enter the number of roles to display (or press Enter to display all): ").strip()
        roles_to_display = int(roles_to_display) if roles_to_display.isdigit() else None

        job_cards = driver.find_elements(By.CLASS_NAME, "job-card-container")
        jobs = []

        # Iterasi berdasarkan jumlah yang diinginkan atau semua jika tidak diatur
        for index, job in enumerate(job_cards):
            if roles_to_display and index >= roles_to_display:
                break
            job_title = job.text.split("\n")[0]
            company_name = job.text.split("\n")[1] if len(job.text.split("\n")) > 1 else "Unknown Company"
            jobs.append({"Job Title": job_title, "Company": company_name})

        # Tambahkan pagination jika ada lebih banyak pekerjaan
        try:
            next_button = driver.find_element(By.CLASS_NAME, "next-page-class-name")  # Ubah sesuai nama kelas sebenarnya
            while next_button and (not roles_to_display or len(jobs) < roles_to_display):
                next_button.click()
                time.sleep(random.uniform(2, 4))
                job_cards = driver.find_elements(By.CLASS_NAME, "job-card-container")
                for index, job in enumerate(job_cards):
                    if roles_to_display and len(jobs) >= roles_to_display:
                        break
                    job_title = job.text.split("\n")[0]
                    company_name = job.text.split("\n")[1] if len(job.text.split("\n")) > 1 else "Unknown Company"
                    jobs.append({"Job Title": job_title, "Company": company_name})
                next_button = driver.find_element(By.CLASS_NAME, "next-page-class-name")  # Ubah sesuai nama kelas sebenarnya
        except Exception:
            logging.info("No more pages or pagination error occurred.")

        return jobs

    except Exception as e:
        logging.error(f"Error during job search: {e}")
        print("Error during job search.")
        return []


def apply_jobs(driver, use_existing_resume, pdf_path, settings):
    try:
        wait = WebDriverWait(driver, 10)
        job_cards = driver.find_elements(By.CLASS_NAME, "job-card-container")

        applied_jobs = []

        for index, job in enumerate(job_cards):
            job.click()
            time.sleep(random.uniform(2, 4))  # Wait for job details to load

            try:
                # Use explicit waits to ensure elements are available
                job_title_element = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".job-card-list__title")))
                company_name_element = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".job-card-container__company-name")))
                job_title = job_title_element.text if job_title_element else "Unknown Job Title"
                company_name = company_name_element.text if company_name_element else "Unknown Company"
                print(f"\nProcessing Job {index + 1}: {job_title} at {company_name}")
                
                apply_now = input("Do you want to apply for this job? (y/n): ").strip().lower()

                if apply_now == 'y':
                    logging.info(f"Attempting to apply for job: {job_title} at {company_name}")
                    try:
                        # Click the 'Easy Apply' button
                        easy_apply_button = wait.until(EC.element_to_be_clickable((By.CLASS_NAME, "jobs-apply-button")))
                        easy_apply_button.click()
                        logging.info("Clicked 'Easy Apply' button.")

                        # Upload resume if not using an existing one
                        if not use_existing_resume:
                            upload_button = wait.until(EC.presence_of_element_located((By.XPATH, "//input[@type='file']")))
                            upload_button.send_keys(pdf_path)
                            logging.info("Uploaded custom resume.")

                        # Click the 'Submit' button
                        submit_button = wait.until(EC.element_to_be_clickable(
                            (By.XPATH, "//button[contains(@class, 'artdeco-button--primary')]")
                        ))
                        submit_button.click()
                        logging.info("Submitted the application.")

                        # Check for confirmation (if available)
                        try:
                            confirmation_element = wait.until(
                                EC.presence_of_element_located((By.CLASS_NAME, "confirmation-message-class"))
                            )
                            if confirmation_element:
                                print(f"Application for {job_title} at {company_name} was successful.")
                                logging.info(f"Application for {job_title} at {company_name} was successful.")
                                applied_jobs.append({"Job Title": job_title, "Company": company_name})
                        except Exception:
                            logging.warning(f"Could not confirm application success for {job_title} at {company_name}.")

                        # Close the modal if it appears
                        try:
                            close_button = wait.until(EC.element_to_be_clickable(
                                (By.CLASS_NAME, "artdeco-modal__dismiss")
                            ))
                            close_button.click()
                            logging.info("Closed the application modal.")
                        except Exception as e:
                            logging.warning(f"Could not close application modal: {e}")

                    except Exception as e:
                        logging.warning(f"Could not complete Easy Apply for job: {job_title}. Reason: {e}")
                else:
                    logging.info(f"Skipped application for job: {job_title} at {company_name}")

                # Move to the next job in the list
                print("Moving to the next job...")

            except Exception as e:
                logging.warning(f"Error accessing job details: {e}")

        if applied_jobs:
            print("\nSuccessfully applied to the following jobs:")
            for job in applied_jobs:
                print(f"- {job['Job Title']} at {job['Company']}")
                logging.info(f"Applied to: {job['Job Title']} at {job['Company']}")
        else:
            print("\nNo applications were successfully submitted.")

        # After processing all jobs, return to the main search page
        print("Returning to the main search results...")

    except Exception as e:
        logging.error(f"Error during job application process: {e}")
        print("Error during job application.")


# Main function
def main():
    settings = load_settings()
    
    username = settings.get("username")
    password = settings.get("password")

    if not username or not password:
        username = input("Enter your LinkedIn Username: ")
        password = input("Enter your LinkedIn Password: ")
        settings["username"] = username
        settings["password"] = password
        save_settings(settings)

    driver = setup_driver()
    login_linkedin(driver, username, password)

    while True:
        keyword = input("Enter job search keyword: ")
        location = input("Enter job location: ")
        easy_apply = input("Apply Easy Apply filter? (y/n): ").strip().lower() == 'y'
        job_type = input("Enter job type (remote/hybrid/onsite): ").strip().lower()

        jobs = search_jobs(driver, keyword, location, easy_apply, job_type)
        if jobs:
            print(f"\nTotal jobs found: {len(jobs)}")
            for index, job in enumerate(jobs):
                print(f"{index + 1}. {job['Job Title']} at {job['Company']}")

            apply_all = input("Do you want to apply to all jobs automatically? (y/n): ").strip().lower()
            use_existing_resume = input("Use existing resume on LinkedIn? (y/n): ").strip().lower() == 'y'
            pdf_path = None

            if not use_existing_resume:
                pdf_path = input("Enter the path to your PDF resume: ").strip()
                if not os.path.exists(pdf_path):
                    print("Invalid file path. Exiting.")
                    driver.quit()
                    return

            if apply_all == 'y':
                apply_jobs(driver, use_existing_resume, pdf_path, settings)
            else:
                for job in jobs:
                    print(f"\nJob: {job['Job Title']} at {job['Company']}")
                    apply_now = input("Do you want to apply for this job? (y/n): ").strip().lower()
                    if apply_now == 'y':
                        apply_jobs(driver, use_existing_resume, pdf_path, settings)

        continue_search = input("Do you want to perform another search? (y/n): ").strip().lower()
        if continue_search != 'y':
            break

    driver.quit()

if __name__ == "__main__":
    main()