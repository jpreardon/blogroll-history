# Blogroll History

This project attempts to visually display how a person's blog roll has changed over time using backups of OPML files.

This evolved from an [Observable Notebook](https://observablehq.com/d/5d1882f77f5a6ce4), which has more of the story and process.

The opml_to_json.py file parses all of the .opml files in a directory and produces a single JSON file suitable for use with a D3 barbell chart.

The script runs incrementally. The output JSON stores a `last_processed_date` in its metadata, and on subsequent runs the script only processes OPML files with dates newer than that value. If there is nothing new to process, the script exits without touching the output file. A backup is only created when there is actual new work to do.

Entries for the same blog are automatically deduplicated on each run. Consecutive date ranges that touch or overlap are merged into a single entry. Genuine gaps — where a blog was removed from the blogroll and later re-added — are preserved as separate entries.

## Instructions

Run the script from the command line:

```
python3 opml-to-json.py <input_directory> <output_json_file> <target_outline_texts> [<url_map_file>]
```

**Parameters**

* `input_directory` — relative path to the directory containing OPML files
* `output_json_file` — path to the output JSON file; will be created if it doesn't exist, backed up if it does. To force a full reset, delete or move this file before running.
* `target_outline_texts` — comma-separated list of outline names to include; all others are ignored
* `url_map_file` _(optional)_ — path to a JSON file mapping old URLs to new ones. Useful when a blog has changed its URL. The script ignores protocol (http vs. https) and trailing slashes when comparing URLs. See url-map.json.example for the expected format.

**Example**

```
python3 opml-to-json.py olde-blogrolls/opml blogroll-history.json "Blogs,Feeds" url-map.json
```

Here's an example of the output: [https://jpreardon.com/data/](https://jpreardon.com/data/)