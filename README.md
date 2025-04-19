# Blogroll History

This project attempts to visually display how a person's blog roll has changed over time using backups of OPML files.

This evolved from an [Observable Notebook](https://observablehq.com/d/5d1882f77f5a6ce4), which has more of the story and process.

The opml_to_json.py file parses all of the .opml files in a directory using the following parameters:

* Input directory (relative path to directory containing OPML files)
* Output JSON file (will create if it doesn't exist, will backup if it does) - if a "full reset" is desired, ensure this file doesn't exist
* Target outlines (comma separated list of outlines to include, all others will be ignored)

Here's an example of the output. Yes, some work needs to be done to make this more useable.

![screenshot of blogroll history graph](https://jpreardon.com/wp-content/uploads/2024/11/jpr-blogroll.png)