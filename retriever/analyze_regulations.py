import os
import json
import re
import threading
import logging
from concurrent.futures import ThreadPoolExecutor
from lxml import etree
from nltk.sentiment.vader import SentimentIntensityAnalyzer
import multiprocessing

# Logging Configuration
logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.DEBUG,
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# Analysis Configuration
RESTRICTIVE_WORDS = {"shall", "must", "penalty", "prohibited", "required", "restrict", "forbid"}
sia = SentimentIntensityAnalyzer()

# XML Processing Functions
def analyze_xml_content(file_path):
    logger.info(f"Analyzing file: {file_path}")
    try:
        tree = etree.parse(file_path)
        text_content = tree.xpath('//text()')
        full_text = " ".join(t.strip() for t in text_content if t.strip())
        logger.debug(f"Extracted text from {file_path}: {len(full_text)} chars, sample: {full_text[:100]}")

        words = [word.lower() for word in re.split(r'\s+', full_text) if word]
        word_count = len(words)
        restrictive_count = sum(word in RESTRICTIVE_WORDS for word in words)
        restrictiveness = restrictive_count / word_count if word_count > 0 else 0
        sentiment = sia.polarity_scores(full_text[:100000])["compound"] if full_text else 0

        sentences = re.split(r'[.!?]\s+', full_text)
        sentence_lengths = [len(re.split(r'\s+', s)) for s in sentences if s.strip()]
        avg_sentence_length = sum(sentence_lengths) / len(sentence_lengths) if sentence_lengths else 0

        result = {
            "word_count": word_count,
            "restrictiveness": restrictiveness,
            "sentiment": sentiment,
            "avg_sentence_length": avg_sentence_length
        }
        logger.debug(f"Analysis result for {file_path}: {result}")
        return result
    except Exception as e:
        logger.error(f"Failed to analyze {file_path}: {str(e)}")
        return None

def get_existing_analysis(file_path, replace_existing=False):
    directory = os.path.dirname(file_path)
    output_file = os.path.join(directory, "regulation_analysis.json")
    filename = os.path.basename(file_path)

    if not replace_existing and os.path.exists(output_file):
        try:
            with open(output_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                for file_data in data["files"]:
                    if file_data["file_name"] == filename:
                        logger.info(f"Found existing analysis for {file_path}")
                        return file_data
        except Exception as e:
            logger.error(f"Error reading {output_file}: {str(e)}")
    return None

# Path Utilities
def extract_parent_agency(file_path):
    parts = file_path.split(os.sep)
    for i, part in enumerate(parts):
        if part == "data" and i + 1 < len(parts):
            return parts[i + 1]
    return "unknown"

def extract_year(file_path):
    match = re.search(r"\b(20\d{2})\b", file_path)
    return int(match.group(1)) if match else None

# File Processing
def process_file(file_path, results, dir_results, lock, processed_files, replace_existing=False):
    existing_analysis = get_existing_analysis(file_path, replace_existing)
    if existing_analysis and not replace_existing:
        analysis = existing_analysis
        logger.info(f"Using existing data for {file_path}: {analysis}")
    else:
        analysis = analyze_xml_content(file_path)
        if analysis is None:
            return

    parent_agency = extract_parent_agency(file_path)
    year = extract_year(file_path)
    directory = os.path.dirname(file_path)
    filename = os.path.basename(file_path)

    if year is None:
        logger.warning(f"Could not extract year from {file_path}, adding to dir_results only")
    else:
        with lock:
            if file_path not in processed_files or replace_existing:
                if parent_agency not in results:
                    results[parent_agency] = {}
                if year not in results[parent_agency]:
                    results[parent_agency][year] = {
                        "word_count": 0,
                        "restrictiveness": 0,
                        "sentiment": 0,
                        "avg_sentence_length": 0,
                        "file_count": 0
                    }
                results[parent_agency][year]["word_count"] += analysis["word_count"]
                results[parent_agency][year]["restrictiveness"] += analysis["restrictiveness"] * analysis["word_count"]
                results[parent_agency][year]["sentiment"] += analysis["sentiment"] * analysis["word_count"]
                results[parent_agency][year]["avg_sentence_length"] += analysis["avg_sentence_length"] * analysis["word_count"]
                results[parent_agency][year]["file_count"] += 1
                processed_files.add(file_path)
                logger.info(f"Added {file_path}: {analysis['word_count']} words to {parent_agency}/{year}")

    # Always update dir_results for per-directory output
    with lock:
        if directory not in dir_results:
            dir_results[directory] = {"total_word_count": 0, "files": []}
        file_data = {"file_name": filename, **analysis}
        if not any(f["file_name"] == filename for f in dir_results[directory]["files"]):
            dir_results[directory]["files"].append(file_data)
            dir_results[directory]["total_word_count"] += analysis["word_count"]

def process_directory(root_dir, max_workers=None, replace_existing=False):
    logger.info(f"Processing directory: {root_dir} (replace_existing={replace_existing})")
    if not os.path.exists(root_dir):
        logger.error(f"Root directory does not exist: {root_dir}")
        return

    if max_workers is None:
        max_workers = multiprocessing.cpu_count()

    results = {}
    dir_results = {}
    lock = threading.Lock()
    processed_files = set()

    # Collect XML files
    xml_files = [os.path.join(dirpath, f) for dirpath, _, filenames in os.walk(root_dir)
                 for f in filenames if f.endswith(".xml")]
    logger.info(f"Found {len(xml_files)} XML files")

    if not xml_files:
        logger.warning("No XML files found")
        return

    # Process files
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        executor.map(lambda fp: process_file(fp, results, dir_results, lock, processed_files, replace_existing), xml_files)

    # Save per-directory results
    for directory, data in dir_results.items():
        output_file = os.path.join(directory, "regulation_analysis.json")
        try:
            os.makedirs(directory, exist_ok=True)
            rounded_data = {
                "total_word_count": data["total_word_count"],
                "files": [
                    {
                        "file_name": f["file_name"],
                        "word_count": f["word_count"],
                        "restrictiveness": round(f["restrictiveness"], 3),
                        "sentiment": round(f["sentiment"], 3),
                        "avg_sentence_length": round(f["avg_sentence_length"], 3)
                    }
                    for f in data["files"]
                ]
            }
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(rounded_data, f, indent=4)
            logger.info(f"Saved per-directory results to {output_file}")
        except Exception as e:
            logger.error(f"Failed to save {output_file}: {str(e)}")

    # Scale restrictiveness (optional, uncomment if needed)
    all_restrictiveness = [f["restrictiveness"] for dir_data in dir_results.values() for f in dir_data["files"]]
    min_restrictiveness = min(all_restrictiveness) if all_restrictiveness else 0
    max_restrictiveness = max(all_restrictiveness) if all_restrictiveness else 0
    range_restrictiveness = max_restrictiveness - min_restrictiveness or 1

    # Finalize aggregated results
    aggregated_data = []
    for agency, years in results.items():
        agency_data = {"agency": agency, "data": []}
        for year, stats in years.items():
            total_words = stats["word_count"]
            if total_words > 0 and stats["file_count"] > 0:
                raw_restrictiveness = stats["restrictiveness"] / total_words
                scaled_restrictiveness = ((raw_restrictiveness - min_restrictiveness) / range_restrictiveness) * 100
                agency_data["data"].append({
                    "year": year,
                    "wordCount": total_words,
                    "avgSentenceLength": stats["avg_sentence_length"] / total_words,
                    "restrictiveness": scaled_restrictiveness,  # Use raw_restrictiveness if scaling not needed
                    "sentiment": stats["sentiment"] / total_words,
                    "fileCount": stats["file_count"]
                })
                logger.info(f"{agency} {year}: {total_words} words, {stats['file_count']} files")
        if agency_data["data"]:
            aggregated_data.append(agency_data)

    # Save aggregated results
    output_file = os.path.join(root_dir, "aggregated_analysis_by_year_and_agency.json")
    try:
        os.makedirs(root_dir, exist_ok=True)
        rounded_aggregated_data = [
            {
                "agency": agency_data["agency"],
                "data": [
                    {
                        "year": year_data["year"],
                        "wordCount": year_data["wordCount"],
                        "avgSentenceLength": round(year_data["avgSentenceLength"], 3),
                        "restrictiveness": round(year_data["restrictiveness"], 3),
                        "sentiment": round(year_data["sentiment"], 3),
                        "fileCount": year_data["fileCount"]
                    }
                    for year_data in agency_data["data"]
                ]
            }
            for agency_data in aggregated_data
        ]
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(rounded_aggregated_data, f, indent=4)
        logger.info(f"Saved aggregated results to {output_file}")
    except Exception as e:
        logger.error(f"Failed to save {output_file}: {str(e)}")

# Main Execution
if __name__ == "__main__":
    ROOT_DIRECTORY = r".\data"
    process_directory(ROOT_DIRECTORY, replace_existing=True)
    logger.info("Processing complete")