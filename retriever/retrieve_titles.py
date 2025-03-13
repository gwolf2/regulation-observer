import os
import time
import requests
import boto3
from botocore.exceptions import NoCredentialsError
from datetime import datetime
from pathlib import Path

# Load environment variables
from dotenv import load_dotenv

load_dotenv()

# Hardcoded dates
# TODO --- add more dates if fetching goes well...
MARCH_DATE_2025 = "2025-03-01"
MARCH_DATE_2024 = "2024-03-01"
MARCH_DATE_2023 = "2023-03-01"

# Define the title numbers to fetch
# TODO --- don't define these explicity?
TITLE_NUMBERS = [
    "1",
    "2",
    "3",
    "4",
    "5",
    "6",
    "7",
    "8",
    "9",
    "10",
    "11",
    "12",
    "13",
    "14",
    "15",
    "16",
    "17",
    "18",
    "19",
    "20",
    "21",
    "22",
    "23",
    "24",
    "25",
    "26",
    "27",
    "28",
    "29",
    "30",
    "31",
    "32",
    "33",
    "34",
    "35",
    "36",
    "37",
    "38",
    "39",
    "40",
    "41",
    "42",
    "43",
    "44",
    "45",
    "46",
    "47",
    "48",
    "49",
    "50",
]


# S3 client
s3_client = boto3.client(
    "s3",
    region_name=os.getenv("AWS_REGION"),
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
)

# def format_date(date):
#     """Format date as YYYY-MM-DD"""
#     return date.strftime('%Y-%m-%d')


def delay(seconds):
    """Creates a delay of specified seconds"""
    time.sleep(seconds)


def download_title(title_number, date):
    try:
        base_url = "https://www.ecfr.gov/api"  # TODO - put in settings file

        file_name = f"title-{title_number}_{date}.xml"
        file_path = Path(f"data/{file_name}")
        if file_path.exists():
            print(
                f"Title {title_number} for date {date} already downloaded - skipping download"
            )
            return None
        else:
            print(
                f"Title {title_number} for date {date} not yet downloaded - downloading"
            )

        url = f"{base_url}/versioner/v1/full/{date}/title-{title_number}.xml"
        print(f"Downloading title {title_number} for date {date} from {url}")

        response = requests.get(url, timeout=60)
        response.raise_for_status()

        print(f"Downloaded title {title_number} for date {date}")

        with open(file_name, "wb") as file:
            file.write(response.content)
        return response.content
    except requests.RequestException as error:
        print(f"Failed to download title {title_number} for date {date}")
        return None


def upload_to_s3(data, key):
    """Upload data to S3"""
    try:
        s3_client.put_object(
            Bucket=os.getenv("AWS_S3_BUCKET"),
            Key=key,
            Body=data,
            ContentType="application/xml",
        )
        print(f"Successfully uploaded {key} to S3")
        return True
    except NoCredentialsError as error:
        print(f"Error uploading to S3: {error}")
        return False


def process_single_title(title_number, date):
    """Process a single title for a specific date - download and upload to S3"""
    try:
        # Download the title for the specific date
        title_data = download_title(title_number, date)

        return

        if not title_data:
            return {"title": title_number, "success": False}

        # Create the key with the date prefix: YYYY-MM-DD-title-N.xml
        key = f"{date}-title-{title_number}.xml"
        print(f"Uploading to S3 with key: {key}")

        upload_success = upload_to_s3(title_data, key)

        if not upload_success:
            print(f"Failed to upload {key}")
            return {"title": title_number, "success": False}
        else:
            print(f"Successfully uploaded {key}")
            return {"title": title_number, "success": True}
    except Exception as error:
        print(f"Error processing title {title_number}: {error}")
        return {"title": title_number, "success": False}


def download_and_upload_all_titles():
    """Download all titles and upload to S3 for multiple date periods (2023, 2024, 2025)"""
    # dates = [MARCH_DATE_2023, MARCH_DATE_2024, MARCH_DATE_2025]
    dates = [MARCH_DATE_2025]  # TODO - retrieve data for more years
    all_results = []

    for date in dates:
        print(f"\n=== PROCESSING TITLES FOR DATE: {date} ===\n")

        for title_number in TITLE_NUMBERS:
            print(f"\nProcessing title {title_number} for date {date}...")

            result = process_single_title(title_number, date)
            # all_results.append({**result, 'date': date})

            # if not result['success']:
            #     print(f"Title {title_number} for {date} processing was unsuccessful - continuing with next title")
            # else:
            #     print(f"Title {title_number} for {date} successfully downloaded and uploaded to S3")

            if title_number != TITLE_NUMBERS[-1]:
                time.sleep(2)

        print(f"\n=== COMPLETED ALL TITLES FOR DATE: {date} ===\n")

    success_count = sum(1 for result in all_results if result["success"])
    failed_count = len(all_results) - success_count

    print("\n=== DOWNLOAD SUMMARY ===")
    print(f"Total files processed: {len(all_results)}")
    print(f"Successfully processed: {success_count}")
    print(f"Failed/Skipped: {failed_count}")

    if failed_count > 0:
        print("\nFailed files:")
        for result in all_results:
            if not result["success"]:
                print(f"- Title {result['title']} for date {result['date']}")

    return {"success": success_count, "failed": failed_count, "titles": all_results}


if __name__ == "__main__":
    download_and_upload_all_titles()
