import urllib3
from urllib.parse import urljoin, quote
from bs4 import BeautifulSoup
import pandas as pd
import requests
from datetime import datetime
import concurrent.futures
import time
from dotenv import load_dotenv
import os
import logging
from sqlalchemy import create_engine, types
from sqlalchemy.exc import SQLAlchemyError
import re
import pytz
import psycopg2 
from psycopg2 import sql, extras 

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class JobScraper:
    def __init__(self):
        self.data = None
        self.load_credentials()
        self.db_params = self.load_db_credentials()
        self.engine = self.create_engine()

    def load_credentials(self):
        load_dotenv()
        self.email = os.getenv('EMAIL')
        self.password = os.getenv('PASSWORD')
        if not self.email or not self.password:
            logger.error("Email or password not set in environment variables.")

    def load_db_credentials(self):
        load_dotenv()
        return {
            'dbname': os.getenv('DB_NAME'),
            'user': os.getenv('DB_USER'),
            'password': os.getenv('DB_PASSWORD'),
            'host': os.getenv('DB_HOST'),
            'port': os.getenv('DB_PORT')
        }

    def create_engine(self):
        db_url = f"postgresql+psycopg2://{self.db_params['user']}:{self.db_params['password']}@{self.db_params['host']}:{self.db_params['port']}/{self.db_params['dbname']}"
        return create_engine(db_url)

    def fetch_url(self, url, headers=None, params=None, verify=True):
        try:
            response = requests.get(url, headers=headers, params=params, verify=verify)
            response.raise_for_status()
            return response
        except requests.RequestException as e:
            logger.error(f"Request to {url} failed: {e}")
            return None

    def parse_azercell(self):
        logger.info("Started scraping Azercell")
        url = "https://www.azercell.com/az/about-us/career.html"
        response = self.fetch_url(url)
        if response:
            soup = BeautifulSoup(response.text, "html.parser")
            vacancies_section = soup.find("section", class_="section_vacancies")
            if vacancies_section:
                job_listings = vacancies_section.find_all("a", class_="vacancies__link")
                job_titles = [job.find("h4", class_="vacancies__name").text for job in job_listings]
                job_locations = [job.find("span", class_="vacancies__location").text.strip() for job in job_listings]
                job_links = [job["href"] for job in job_listings]
                df = pd.DataFrame({'company': 'azercell', "vacancy": job_titles, "location": job_locations, "apply_link": job_links})
                logger.info("Scraping completed for Azercell")
                return df
            else:
                logger.warning("Vacancies section not found on the Azercell page.")
        return pd.DataFrame(columns=['company', 'vacancy', 'location', 'apply_link'])

    def get_data(self):
        methods = [self.parse_azercell]
        results = []
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future_to_method = {executor.submit(method): method for method in methods}
            for future in concurrent.futures.as_completed(future_to_method):
                method = future_to_method[future]
                try:
                    result = future.result()
                    if not result.empty:
                        results.append(result)
                except Exception as e:
                    logger.error(f"Error executing {method.__name__}: {e}")

        if results:
            self.data = pd.concat(results, ignore_index=True)
            self.data['scrape_date'] = datetime.now()
        else:
            self.data = pd.DataFrame(columns=['company', 'vacancy', 'location', 'apply_link', 'scrape_date'])

        return self.data

    def fetch_existing_jobs(self):
        query = """
        SELECT title AS vacancy, company
        FROM jobs_jobpost
        WHERE is_scraped = TRUE
        """
        return pd.read_sql_query(query, self.engine)

    def save_to_db(self, df, batch_size=100):
        try:
            existing_jobs = self.fetch_existing_jobs()
            new_jobs = df.merge(existing_jobs, on=['vacancy', 'company'], how='left', indicator=True)
            new_jobs = new_jobs[new_jobs['_merge'] == 'left_only'].drop(columns=['_merge'])

            if new_jobs.empty:
                logger.info("No new jobs to insert.")
                return

            with psycopg2.connect(**self.db_params) as conn:
                with conn.cursor() as cur:
                    insert_query = sql.SQL("""
                        INSERT INTO jobs_jobpost (title, description, company, location, posted_by_id, is_scraped, is_premium, premium_days, priority_level, posted_at, deleted, apply_link)
                        VALUES %s
                    """)

                    data_tuples = [
                        (
                            row['vacancy'][:500],
                            '',
                            row['company'][:500],
                            row['location'][:500],
                            1,
                            True,
                            False,
                            0,
                            99,
                            datetime.now(),
                            False,
                            row['apply_link'][:1000]
                        )
                        for _, row in new_jobs.iterrows()
                    ]

                    extras.execute_values(cur, insert_query, data_tuples, template=None, page_size=batch_size)
                    conn.commit()
                    logger.info("Data successfully saved to the database.")
        except (Exception, psycopg2.DatabaseError) as error:
            logger.error(f"Error saving data to the database: {error}")

def main():
    job_scraper = JobScraper()
    data = job_scraper.get_data()

    if data.empty:
        logger.warning("No data scraped to save to the database.")
        return

    logger.info(f"Data to be saved: {data}")

    job_scraper.save_to_db(data)

if __name__ == "__main__":
    main()
