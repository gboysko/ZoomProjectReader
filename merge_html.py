import json
import sys
from string import Template
from jinja2 import Environment, FileSystemLoader, select_autoescape

# Our Jinja2 Environment
env = Environment(
    loader=FileSystemLoader("."),
    autoescape=select_autoescape()
)

if __name__ == "__main__":
    # Look for command line argument of file name...
    if len(sys.argv[1:]) < 3:
        # Status...
        print("Missing files: TEMPLATE_FILE JSON_FILE OUTPUT_HTML\n")
    else:
        # Load the Template file
        sys.stdout.write(Template('Loading the Template file: $html_file...').substitute(html_file=sys.argv[1]))

        # Load the template file
        template = env.get_template(sys.argv[1])
        if not template:
            # Status
            print("Error! Unable to locate template file!\n")
        else:
            # Status
            print("OK")

            # Open the JSON file
            sys.stdout.write(Template("Loading the JSON file: $json_file...").substitute(json_file=sys.argv[2]))
            with open(sys.argv[2], "r") as json_file:
                # Get the JSON
                json_root = json.load(json_file)

                # Status
                print("OK")

            # Open the OUTPUT file for writing
            sys.stdout.write(Template("Opening the HTML file: $output_file...").substitute(output_file=sys.argv[3]))
            with open(sys.argv[3], "w") as output_file:
                # Render the template!
                output_html_text = template.render(json_root)

                # Write it...
                output_file.write(output_html_text)

                # Status
                print("OK")
