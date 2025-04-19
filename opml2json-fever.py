import xml.etree.ElementTree as ET
import json
import sys
import os

'''
What's going on here?

Need to convert OPML into JSON:

    {
        [
            {
                name:"[blog name]",
                date:"[YYYY-MM-DD]",
                url:"[url]"
            },
        ]
    }

The ChatGPT generated code below works, but I need to filter out some stuff to simplify.

'''


import xml.etree.ElementTree as ET
import json
import sys
import os

def parse_outline(outline_element):
    """Parse an outline element into a dictionary with specific fields: name, date, and url."""
    # Extract the required fields
    name = outline_element.attrib.get("text", "")
    date = sys.argv[3]
    url = outline_element.attrib.get("htmlUrl", "")
    
    # Only include the dictionary if 'name' and 'url' are present
    if name and url:
        return {
            "name": name,
            "date": date,
            "url": url
        }
    return None

def find_outline_by_title(outline_elements, title):
    """Find an outline element with a specific title attribute."""
    for outline in outline_elements:
        if outline.attrib.get("text") == title:
            return outline
        # Recursively search child outlines
        result = find_outline_by_title(outline.findall("outline"), title)
        if result is not None:
            return result
    return None

def opml_to_json(opml_file_path, json_file_path, title="Kindling"):
    """Convert specific OPML outline to JSON list of dictionaries based on title."""
    try:
        # Parse the OPML file
        tree = ET.parse(opml_file_path)
        root = tree.getroot()
        
        # Ensure the root element is an OPML document
        if root.tag.lower() != "opml":
            raise ValueError("The file does not appear to be a valid OPML document.")
        
        # Parse the body
        body = root.find("body")
        if body is None:
            raise ValueError("The OPML file does not contain a body element.")
        
        # Find the specific outline with the given title
        target_outline = find_outline_by_title(body.findall("outline"), title)
        if target_outline is None:
            raise ValueError(f"No outline found with the title '{title}'")
        
        # Collect the list of items
        items = [parse_outline(outline) for outline in target_outline.findall("outline")]
        items = [item for item in items if item is not None]  # Filter out None entries

        # Write the result to a JSON file
        with open(json_file_path, "w", encoding="utf-8") as json_file:
            json.dump(items, json_file, ensure_ascii=False, indent=2)
        
        print(f"Conversion successful! JSON saved to {json_file_path}")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    # Check if enough arguments are provided
    if len(sys.argv) != 4:
        print("Usage: python opml_to_json.py <input_opml_file> <output_json_file> <date>")
        sys.exit(1)

    # Get file paths from command-line arguments
    opml_file_path = sys.argv[1]
    json_file_path = sys.argv[2]

    # Check if the OPML file exists
    if not os.path.isfile(opml_file_path):
        print(f"Error: The file '{opml_file_path}' does not exist.")
        sys.exit(1)

    # Run the conversion
    opml_to_json(opml_file_path, json_file_path)
