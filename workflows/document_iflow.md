# Workflow: Document an iFlow

## Objective
Read an exported iFlow .zip and generate full markdown documentation.

## Inputs
- iFlow .zip file in input/ folder

## Steps
1. Run tools/unzip_iflow.py with the zip filename as argument
2. Run tools/parse_iflow_xml.py → produces tmp/parsed.json
3. Run tools/parse_groovy.py → appends script summaries
4. Run tools/generate_markdown.py → writes to output/

## Edge Cases
- If no .groovy file: skip, note "no custom scripts found"
- If parameters.prop is empty: skip parameters section
- If mapping is XSLT: parse XSL file instead of Groovy

## Expected Output
Single markdown file in output/ named after the iFlow.