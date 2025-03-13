import logging
import requests
import time
from pathlib import Path
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
from threading import Lock
from retrieve_agencies import get_agency_objects

# Configure logging (thread-safe by default in Python)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - [%(threadName)s] - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# Constants
BASE_URL = "https://www.ecfr.gov/api"  # TODO: Move to settings file
BASE_DATE = "03-01"  # Base month and day for regulation downloads
TIMEOUT = 15  # Fixed timeout in seconds
MAX_THREADS = 1  # Limit concurrent threads to avoid overwhelming the API

class DownloadStats:
    """Class to track download statistics with thread-safe updates"""
    def __init__(self):
        self.existing_files = 0
        self.new_downloads = 0
        self.failed_downloads = 0
        self._lock = Lock()  # Thread lock for safe updates

    def increment_existing(self):
        with self._lock:
            self.existing_files += 1

    def increment_new(self):
        with self._lock:
            self.new_downloads += 1

    def increment_failed(self):
        with self._lock:
            self.failed_downloads += 1

def construct_filename(cfr_reference):
    """Generate filename based on CFR reference components."""
    return f"t-{cfr_reference.title}_st-{cfr_reference.subtitle}_c-{cfr_reference.chapter}_sc-{cfr_reference.subchapter}.xml"

def construct_filepath(agency_slug, cfr_reference, date, parent_agency_slug=None):
    """Construct the full filepath for saving the regulation XML."""
    filename = construct_filename(cfr_reference)
    if parent_agency_slug:
        return Path(f"./data/{parent_agency_slug}/{agency_slug}/{date}/{filename}")
    return Path(f"./data/{agency_slug}/{date}/{filename}")

def build_url(base_url, date, cfr_reference):
    """Build the complete URL with query parameters for the eCFR API."""
    url = f"{base_url}/versioner/v1/full/{date}/title-{cfr_reference.title}.xml"
    
    params = []
    if cfr_reference.subtitle is not None:
        params.append(f"subtitle={cfr_reference.subtitle}")
    if cfr_reference.chapter is not None:
        params.append(f"chapter={cfr_reference.chapter}")
    if cfr_reference.subchapter is not None:
        params.append(f"subchapter={cfr_reference.subchapter}")
    
    if params:
        url += "?" + "&".join(params)
    return url

def download_regulation(agency_slug, cfr_reference, date, parent_agency_slug=None, stats=None):
    """Download a single regulation from eCFR API and save it to disk with retries."""
    file_path = construct_filepath(agency_slug, cfr_reference, date, parent_agency_slug)
    file_path.parent.mkdir(parents=True, exist_ok=True)

    if file_path.exists():
        #logger.info(f"Regulation already downloaded - skipping download. File path: {file_path}")
        stats.increment_existing()
        return None

    url = build_url(BASE_URL, date, cfr_reference)
    logger.info(f"Starting download attempt for regulation from {url}")

    max_attempts = 1
    for attempt in range(max_attempts):
        try:
            response = requests.get(url, timeout=TIMEOUT)
            response.raise_for_status()

            with open(file_path, "wb") as file:
                file.write(response.content)
            
            logger.info(f"Successfully downloaded regulation from {url} on attempt {attempt + 1}")
            stats.increment_new()
            time.sleep(2)
            return response.content

        except requests.RequestException as error:
            if attempt < max_attempts - 1:
                logger.warning(f"Attempt {attempt + 1} failed for {url}: {str(error)}. Retrying...")
                time.sleep(1)
                continue
            else:
                logger.error(f"Failed to download regulation from {url} after {max_attempts} attempts: {str(error)}")
                stats.increment_failed()
                return None

def generate_date_list(years):
    """Generate a list of dates based on the number of years requested."""
    current_year = datetime.now().year
    dates = []
    
    for i in range(years):
        year = current_year - i
        date_str = f"{year}-{BASE_DATE}"
        dates.append(date_str)
    
    return dates

def download_regulations(agencies, years=1):
    """Download regulations for all provided agencies across specified years in parallel."""
    dates = generate_date_list(years)
    stats = DownloadStats()
    logger.info(f"Downloading regulations for {years} years: {dates}")

    # Prepare tasks for parallel execution
    tasks = []
    for date in dates:
        for agency in agencies:
            for cfr_reference in agency.cfr_references:
                tasks.append((agency.slug, cfr_reference, date, agency.parent_slug, stats))

    # Execute downloads in parallel with ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
        logger.info(f"Starting parallel downloads with {MAX_THREADS} threads")
        executor.map(
            lambda task: download_regulation(task[0], task[1], task[2], task[3], task[4]),
            tasks
        )

    return stats

def main(years=1):
    """Main entry point for the script."""
    logger.info(f"Starting regulation download process for {years} years")
    agency_objects = get_agency_objects()
    stats = download_regulations(agency_objects, years)
    
    # Log the final statistics
    logger.info("Regulation download process completed")
    logger.info(f"Download Statistics:")
    logger.info(f"Files already downloaded: {stats.existing_files}")
    logger.info(f"Files downloaded this run: {stats.new_downloads}")
    logger.info(f"Files failed to download: {stats.failed_downloads}")

if __name__ == "__main__":
    main(years=3)