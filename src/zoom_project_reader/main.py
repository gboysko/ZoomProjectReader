import sys
import jsons
from string import Template
from generate_json import ProjectDir, InvalidProjectDirectory
from merge_html import merge_json_and_template
from util import status

# Constants
TEMPLATE_FILE = "template.html"

if __name__ == '__main__':
    # Look for command line argument of file name...
    if len(sys.argv[1:]) < 3:
        # Status...
        print("Missing arguments: PROJECT_DIR EXTRA_JSON_FILE OUTPUT_HTML_FILE")
    else:
        # Diagnostics
        status(Template('Reading "$project_dir"...').substitute(project_dir=sys.argv[1]))

        # Open the project directory for reading...
        try:
            # Get the Project Directory object...
            project_dir = ProjectDir.read_directory(sys.argv[1])

            # Retrieve the project file
            project_file = project_dir.project_file

            # Diagnostics
            print(Template('OK [$num_files files in Project "$name"]').substitute(num_files=project_dir.num_files, name=project_file.project_name))
        except InvalidProjectDirectory as ipd:
            # Diagnostics
            print(Template("Error [$message]").substitute(message=ipd.message))

            # Exit with a failure
            sys.exit(1)

        # Diagnostics...
        status(Template('Loading "$extra_json_file"...').substitute(extra_json_file=sys.argv[2]))

        # Open the extra JSON file for reading
        try:
            with open(sys.argv[2], "r") as extra_json_file:
                # Read the JSON
                extra_json_text = extra_json_file.read()

                # Convert it to a JSON object
                initial_json_obj = jsons.loads(extra_json_text)

                # Enhance class
                project_file.import_extra_info(initial_json_obj)

                # Diagnostics
                print("OK")
        except FileNotFoundError as fnf:
            # Diagnostics
            print(Template("Error [$file does not exist (ignored)]").substitute(file=fnf.filename))

        try:
            # Diagnostics
            status('Generating JSON...')

            # Generate the JSON object for the project
            json_obj = jsons.dump(project_file, strip_privates=True)

            # Diagnostics
            print("OK")

            # Diagnostics
            status('Generating HTML...')

            # Generate the HTML
            output_html_text = merge_json_and_template(TEMPLATE_FILE, json_obj)

            # Diagnostics
            print("OK")

            # Open the OUTPUT file for writing
            status(Template('Saving the file "$output_file"...').substitute(output_file=sys.argv[3]))
            with open(sys.argv[3], "w") as output_file:
                # Write it...
                output_file.write(output_html_text)

                # Status
                print("OK")
        except Exception as exp:
            # Diagnostics
            print(Template("Error [$message]").substitute(message=exp))

            # Exit with a failure
            sys.exit(1)
