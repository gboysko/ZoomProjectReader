import json
import sys
from string import Template
from jinja2 import Environment, FileSystemLoader, select_autoescape, TemplateNotFound
from util import status

# Our Jinja2 Environment
env = Environment(
    loader=FileSystemLoader("."),
    autoescape=select_autoescape()
)

# Merge the objects together and return HTML text
def merge_json_and_template(template_file, json_obj):
    try:
        # Load the template file
        template = env.get_template(template_file)

        # Render the results
        return template.render(json_obj)
    except TemplateNotFound as tnf:
        # Throw an exception
        raise Exception(Template("Unable to locate template: $msg").substitute(msg=tnf))

if __name__ == "__main__":
    # Look for command line argument of file name...
    if len(sys.argv[1:]) < 3:
        # Status...
        print("Missing files: TEMPLATE_FILE JSON_FILE OUTPUT_HTML\n")
    else:
        # Diagnostics
        status(Template("Loading the JSON file: $json_file...").substitute(json_file=sys.argv[2]))

        try:
            # Open the JSON file
            with open(sys.argv[2], "r") as json_file:
                # Get the JSON
                json_root = json.load(json_file)

                # Status
                print("OK")

            # Diagnostics
            status(Template('Loading the Template file: $html_file...').substitute(html_file=sys.argv[1]))

            # Merge JSON with the template, generating HTML text
            output_html_text = merge_json_and_template(sys.argv[1], json_root)

            # Diagnostics
            print("OK")

            # Open the JSON file
            status(Template("Loading the JSON file: $json_file...").substitute(json_file=sys.argv[2]))
            with open(sys.argv[2], "r") as json_file:
                # Get the JSON
                json_root = json.load(json_file)

                # Status
                print("OK")

            # Open the OUTPUT file for writing
            status(Template("Opening the HTML file: $output_file...").substitute(output_file=sys.argv[3]))
            with open(sys.argv[3], "w") as output_file:
                # Write it...
                output_file.write(output_html_text)

                # Status
                print("OK")

        except Exception as exp:
            print(Template("Error: $message").substitute(message=exp.message))

            sys.exit(1)
