import xml.etree.ElementTree as ET
import json
import sys
import os
from datetime import datetime
import html  # Import the html module to unescape HTML codes
import logging  # Use logging for better output control

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def normalize_url(url):
    """
    Normalize a URL by:
    - Converting it to lowercase.
    - Removing the protocol (http or https).
    - Stripping trailing slashes and whitespace.
    Returns an empty string if the URL is None or empty.
    """
    if not url:
        return ""
    url = url.lower().strip()
    url = url.replace("http://", "").replace("https://", "").rstrip("/")
    return url

def load_url_map(url_map_file):
    """
    Load a URL map from a JSON file.
    - The JSON file should contain a list of dictionaries with "old" and "new" URL mappings.
    - Returns a dictionary where keys are normalized "old" URLs and values are "new" URLs.
    - Logs a warning if the file is not provided or does not exist.
    - Raises a ValueError if the file cannot be parsed or is malformed.
    """
    if not url_map_file or not os.path.isfile(url_map_file):
        logging.warning(f"URL map file '{url_map_file}' not provided or does not exist.")
        return {}
    try:
        with open(url_map_file, "r", encoding="utf-8") as file:
            url_map_list = json.load(file)
            return {normalize_url(entry["old"]): entry["new"] for entry in url_map_list}
    except (json.JSONDecodeError, KeyError) as e:
        raise ValueError(f"Error loading URL map: {e}")

def map_url(url, url_map):
    """
    Map a URL to its "new" value using the URL map.
    - If the normalized URL exists in the map, return the mapped value.
    - Otherwise, return the original URL.
    """
    return url_map.get(normalize_url(url), url)

def parse_outline(outline_element, start_date, end_date, url_map):
    """
    Parse an individual outline element from the OPML file.
    - Extracts the "text" (title) and "htmlUrl" (URL) attributes.
    - Maps the URL using the provided URL map.
    - Returns a dictionary with the fields: title, url, start, and end.
    - Logs a warning if required attributes are missing.
    - Returns None if the element is invalid or cannot be parsed.
    """
    try:
        title = outline_element.attrib.get("text", "").strip()
        url = outline_element.attrib.get("htmlUrl", "").strip()
        if not title or not url:
            logging.warning("Outline element missing 'text' or 'htmlUrl' attributes.")
            return None
        return {
            "title": html.unescape(title),
            "url": map_url(url, url_map),
            "start": start_date,
            "end": end_date
        }
    except Exception as e:
        logging.error(f"Error parsing outline element: {e}")
        return None

def opml_to_json(input_dir, output_json, target_outline_texts, url_map_file=None):
    """
    Convert all OPML files in a directory to a single JSON file.
    - Processes all .opml files in the input directory, sorted by date in filenames.
    - Extracts outlines matching the specified target texts.
    - Normalizes URLs and updates existing entries in the JSON output.
    - Backs up the existing JSON output file if it exists.
    - Writes the combined data to the specified JSON output file.
    - Logs progress and errors during processing.
    """
    try:
        # Load the URL map if provided
        url_map = load_url_map(url_map_file)

        # Ensure the input directory exists
        if not os.path.isdir(input_dir):
            raise ValueError(f"The input '{input_dir}' is not a directory.")

        # Load existing data from the output JSON file if it exists
        existing_data = []
        if os.path.isfile(output_json):
            base, ext = os.path.splitext(output_json)
            counter = 1
            while os.path.isfile(f"{base}_{counter}{ext}"):
                counter += 1
            backup_filename = f"{base}_{counter}{ext}"
            os.rename(output_json, backup_filename)
            logging.info(f"Existing output file backed up as {backup_filename}")
            with open(backup_filename, "r", encoding="utf-8") as json_file:
                existing_data = json.load(json_file)

        # Find and sort all .opml files in the input directory
        opml_files = [
            filename for filename in os.listdir(input_dir) if filename.endswith(".opml")
        ]
        opml_files.sort(key=lambda x: datetime.strptime(x.split("-")[1].split(".")[0], "%Y%m%d"))

        # Combine data from all OPML files
        combined_data = existing_data
        for filename in opml_files:
            input_opml = os.path.join(input_dir, filename)
            logging.info(f"Processing file: {input_opml}")

            try:
                # Extract the start and end dates from the filename
                date_str = filename.split("-")[1].split(".")[0]
                start_date = datetime.strptime(date_str, "%Y%m%d").strftime("%Y-%m-%dT00:00:00.000Z")
                end_date = start_date

                # Parse the OPML file
                tree = ET.parse(input_opml)
                root = tree.getroot()
                if root.tag.lower() != "opml":
                    raise ValueError(f"The file '{input_opml}' does not appear to be a valid OPML document.")

                # Find the body element
                body = root.find("body")
                if body is None:
                    raise ValueError(f"The OPML file '{input_opml}' does not contain a body element.")

                # Process target outlines
                for target_text in target_outline_texts:
                    target_outline = body.find(f".//outline[@text='{target_text}']")
                    if target_outline is not None:
                        for outline in target_outline.findall("outline"):
                            item = parse_outline(outline, start_date, end_date, url_map)
                            if item is not None:
                                normalized_item_url = normalize_url(item["url"])
                                existing_item = next(
                                    (x for x in combined_data if normalize_url(x["url"]) == normalized_item_url), None
                                )
                                if existing_item:
                                    # Update existing entry
                                    existing_item["end"] = end_date
                                    if existing_item["title"] != item["title"]:
                                        existing_item["title"] = item["title"]
                                    if existing_item["url"] != item["url"]:
                                        existing_item["url"] = item["url"]
                                else:
                                    # Add new entry
                                    combined_data.append(item)
            except Exception as e:
                logging.error(f"Error processing file '{input_opml}': {e}")

        # Write the combined data to the output JSON file
        with open(output_json, "w", encoding="utf-8") as json_file:
            json.dump(combined_data, json_file, ensure_ascii=False, indent=2)

        logging.info(f"Conversion successful! JSON saved to {output_json}")

    except Exception as e:
        logging.error(f"Error: {e}")

if __name__ == "__main__":
    """
    Main entry point for the script.
    - Expects command-line arguments for input directory, output JSON file, target outline texts, and optional URL map file.
    - Validates arguments and calls the opml_to_json function.
    """
    if len(sys.argv) < 4 or len(sys.argv) > 5:
        logging.error("Usage: python opml_to_json.py <input_directory> <output_json_file> <target_outline_texts> [<url_map_file>]")
        sys.exit(1)

    input_dir = sys.argv[1]
    output_json = sys.argv[2]
    target_outline_texts = sys.argv[3].split(",")
    url_map_file = sys.argv[4] if len(sys.argv) == 5 else None

    opml_to_json(input_dir, output_json, target_outline_texts, url_map_file)