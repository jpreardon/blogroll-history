import xml.etree.ElementTree as ET
import json
import sys
import os
from datetime import datetime
import html  # Import the html module to unescape HTML codes

def normalize_url(url):
    """Normalize a URL by removing the protocol (http or https) and trailing slash."""
    return url.replace("http://", "").replace("https://", "").rstrip("/")

def load_url_map(url_map_file):
    """Load the URL map from a JSON file."""
    if not os.path.isfile(url_map_file):
        raise ValueError(f"The URL map file '{url_map_file}' does not exist.")
    with open(url_map_file, "r", encoding="utf-8") as file:
        return json.load(file)

def map_url(url, url_map):
    """Map a URL to its 'new' value if it exists in the URL map, otherwise return the original URL."""
    for entry in url_map:
        if normalize_url(entry["old"]) == normalize_url(url):
            return entry["new"]
    return url

def parse_outline(outline_element, start_date, end_date, url_map):
    """Parse an outline element into a dictionary with specific fields: title, htmlUrl, start, and end."""
    title = outline_element.attrib.get("text", "")
    url = outline_element.attrib.get("htmlUrl", "")
    
    if title and url:
        return {
            "title": html.unescape(title),  # Convert HTML codes to characters
            "url": map_url(url, url_map),   # Map the URL using the URL map
            "start": start_date,
            "end": end_date
        }
    return None

def opml_to_json(input_dir, output_json, target_outline_texts, url_map_file=None):
    """Convert all OPML files in a directory to JSON."""
    try:
        # Load the URL map if the file is provided
        url_map = load_url_map(url_map_file) if url_map_file else []

        # Ensure the input is a directory
        if not os.path.isdir(input_dir):
            raise ValueError(f"The input '{input_dir}' is not a directory.")

        # Backup the existing output file if it exists
        existing_data = []
        if os.path.isfile(output_json):
            # Generate a new filename with a sequential number
            base, ext = os.path.splitext(output_json)
            counter = 1
            while os.path.isfile(f"{base}_{counter}{ext}"):
                counter += 1
            backup_filename = f"{base}_{counter}{ext}"
            os.rename(output_json, backup_filename)
            print(f"Existing output file backed up as {backup_filename}")

            # Load existing data from the output file
            with open(backup_filename, "r", encoding="utf-8") as json_file:
                existing_data = json.load(json_file)

        # Process all .opml files in the directory, sorted by date in filenames
        opml_files = [
            filename for filename in os.listdir(input_dir) if filename.endswith(".opml")
        ]
        opml_files.sort(key=lambda x: datetime.strptime(x.split("-")[1].split(".")[0], "%Y%m%d"))

        combined_data = existing_data
        for filename in opml_files:
            input_opml = os.path.join(input_dir, filename)
            print(f"Processing file: {input_opml}")

            # Extract the start and end dates from the filename
            date_str = filename.split("-")[1].split(".")[0]  # Extract "20200119" from "fever-20200119.opml"
            start_date = datetime.strptime(date_str, "%Y%m%d").strftime("%Y-%m-%dT00:00:00.000Z")
            end_date = start_date  # Use the same date for now, or modify logic if needed

            # Parse the OPML file
            tree = ET.parse(input_opml)
            root = tree.getroot()

            # Ensure the root element is an OPML document
            if root.tag.lower() != "opml":
                raise ValueError(f"The file '{input_opml}' does not appear to be a valid OPML document.")

            # Parse the body
            body = root.find("body")
            if body is None:
                raise ValueError(f"The OPML file '{input_opml}' does not contain a body element.")

            # Collect all child outlines of the target elements
            for target_text in target_outline_texts:
                target_outline = body.find(f".//outline[@text='{target_text}']")
                if target_outline is not None:
                    for outline in target_outline.findall("outline"):
                        item = parse_outline(outline, start_date, end_date, url_map)
                        if item is not None:
                            # Normalize the URL for comparison
                            normalized_item_url = normalize_url(item["url"])
                            # Check if the URL already exists in the combined data
                            existing_item = next(
                                (x for x in combined_data if normalize_url(x["url"]) == normalized_item_url), None
                            )
                            if existing_item:
                                # Update the end date of the existing item
                                existing_item["end"] = end_date
                                # Update the title if it is different
                                if existing_item["title"] != item["title"]:
                                    existing_item["title"] = item["title"]
                                # Update the URL if it is different
                                if existing_item["url"] != item["url"]:
                                    existing_item["url"] = item["url"]
                            else:
                                # Add the new item
                                combined_data.append(item)

        # Write the combined result to a JSON file
        with open(output_json, "w", encoding="utf-8") as json_file:
            json.dump(combined_data, json_file, ensure_ascii=False, indent=2)

        print(f"Conversion successful! JSON saved to {output_json}")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    # Check if enough arguments are provided
    if len(sys.argv) < 4 or len(sys.argv) > 5:
        print("Usage: python opml_to_json.py <input_directory> <output_json_file> <target_outline_texts> [<url_map_file>]")
        sys.exit(1)

    # Get directory path, target texts, and optional URL map file from command-line arguments
    input_dir = sys.argv[1]
    output_json = sys.argv[2]
    target_outline_texts = sys.argv[3].split(",")  # Split the comma-separated list into an array
    url_map_file = sys.argv[4] if len(sys.argv) == 5 else None

    # Run the conversion
    opml_to_json(input_dir, output_json, target_outline_texts, url_map_file)