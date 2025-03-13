import json
from pathlib import Path
import requests

# Constants
DATA_DIR = "data"
AGENCIES_JSON_FILENAME = "agencies.json"
AGENCIES_API_URL = "https://www.ecfr.gov/api/admin/v1/agencies.json"

# Reserved CFR references as a list of (title, chapter) tuples
RESERVED_CFR_REFERENCES = [
    (7, "XVI"),    # Title 7, Chapter XVI
    (7, "XX"),     # Title 7, Chapter XX
    (14, "VI"),    # Title 14, Chapter VI
    (38, "II"),    # Title 38, Chapter II
    (29, "IX"),    # Title 29, Chapter IX
    (48, "57"),    # Title 48, Chapter 57
    (40, "VII"),   # Title 40, Chapter VII
    (32, "XXVII"), # Title 32, Chapter XXVII
    (32, "XVIII"), # Title 32, Chapter XVIII
    (10, "XVIII"), # Title 10, Chapter XVIII
    (32, "XXVIII") # Title 32, Chapter XXVIII
]

class Agency:
    """Represents an agency with its attributes and hierarchical structure."""
    
    def __init__(
        self,
        name,
        short_name,
        display_name,
        sortable_name,
        slug,
        cfr_references=None,
        children=None,
        parent_slug=None
    ):
        self.name = name
        self.short_name = short_name
        self.display_name = display_name
        self.sortable_name = sortable_name
        self.slug = slug
        self.cfr_references = cfr_references or []
        self.children = children or []
        self.parent_slug = parent_slug

    def __repr__(self):
        return (
            f"Agency(name={self.name}, short_name={self.short_name}, "
            f"display_name={self.display_name}, sortable_name={self.sortable_name}, "
            f"slug={self.slug}, cfr_references={self.cfr_references}, "
            f"children={self.children}, parent_slug={self.parent_slug})"
        )

class CfrReference:
    """Represents a CFR reference with title, subtitle, chapter, and subchapter."""
    
    def __init__(self, title, subtitle=None, chapter=None, subchapter=None):
        self.title = title
        self.subtitle = subtitle
        self.chapter = chapter
        self.subchapter = subchapter

    def __repr__(self):
        return (
            f"CfrReference(title={self.title}, subtitle={self.subtitle}, "
            f"chapter={self.chapter}, subchapter={self.subchapter})"
        )

def is_reserved(cfr_ref):
    """Check if a CFR reference matches a reserved title and chapter pair."""
    chapter_str = str(cfr_ref.chapter) if cfr_ref.chapter is not None else None
    return (cfr_ref.title, chapter_str) in RESERVED_CFR_REFERENCES

def remove_reserved_cfr_references(cfr_list):
    """Filter out reserved CFR references from a list."""
    return [cfr for cfr in cfr_list if not is_reserved(cfr)]

def retrieve_agencies():
    """Retrieve agency data from file or API, caching to file if fetched from API."""
    file_path = Path(DATA_DIR) / AGENCIES_JSON_FILENAME

    # Try to load from local file first
    if file_path.exists():
        with open(file_path, "r") as file:
            return json.load(file)

    # Fetch from API if file doesn't exist
    response = requests.get(AGENCIES_API_URL)
    if response.ok:
        data = response.json()
        agencies = data.get("agencies", [])
        # Cache the result to file
        file_path.parent.mkdir(exist_ok=True)  # Ensure directory exists
        with open(file_path, "w") as file:
            json.dump(agencies, file, indent=4)
        return agencies
    else:
        print(f"Error fetching agencies: {response.status_code} - {response.text}")
        return None

def process_cfr_references(cfr_list):
    """Convert a list of CFR dictionaries into CfrReference objects."""
    return [
        CfrReference(
            title=cfr.get("title"),
            subtitle=cfr.get("subtitle"),
            chapter=cfr.get("chapter"),
            subchapter=cfr.get("subchapter")
        )
        for cfr in cfr_list
    ]

def process_agency(item, parent_slug=None):
    """Convert an agency dictionary into an Agency object with processed children."""
    current_item_slug = item.get("slug")
    
    # Process CFR references and remove reserved ones
    cfr_references = process_cfr_references(item.get("cfr_references", []))
    cfr_references = remove_reserved_cfr_references(cfr_references)

    # Create agency object
    agency = Agency(
        name=item.get("name"),
        short_name=item.get("short_name"),
        display_name=item.get("display_name"),
        sortable_name=item.get("sortable_name"),
        slug=current_item_slug,
        cfr_references=cfr_references,
        children=[],
        parent_slug=parent_slug
    )

    # Recursively process children
    agency.children = [
        process_agency(child, current_item_slug) 
        for child in item.get("children", [])
    ]

    return agency

def flatten_agencies(agencies):
    """Flatten a nested agency structure into a single list."""
    flat_list = []
    for agency in agencies:
        flat_list.append(agency)
        flat_list.extend(flatten_agencies(agency.children))
    return flat_list

def get_agency_objects():
    """Retrieve and process all agencies into a flat list of Agency objects."""
    raw_agencies = retrieve_agencies()
    if not raw_agencies:
        return []

    # Process agencies into objects
    agency_objects = [process_agency(item) for item in raw_agencies]
    
    # Flatten the hierarchy and filter for agencies with CFR references
    flat_list = []
    for agency in agency_objects:
        if agency.cfr_references:  # Only include agencies with CFR references
            flat_list.append(agency)
            flat_list.extend(flatten_agencies(agency.children))
    
    return flat_list

# Example usage
if __name__ == "__main__":
    agencies = get_agency_objects()
    print(f"Processed {len(agencies)} agency objects")