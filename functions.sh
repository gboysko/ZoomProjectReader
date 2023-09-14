function gen_html() {
    # If blank, get out now!
    if [ -z "$1" ]; then
        echo "Missing the base name" >&2
    elif [ ! -f "$1.zdt" ]; then
        echo "The Project file ($1.zdt) does not exist!" >&2
    else
        # Get the base name
        base=$1

        # What is the name of the project file?
        proj_file=${base}.zdt

        # What is the name of our generated JSON file?
        json_file=${base}.json

        # What is the name of our generated HTML file
        html_file=${base}.htm

        # Generate the JSON
        python3 generate_json.py $proj_file ${base}_extra.json $json_file

        # Did it fail?
        if [ $? -ne 0 ]; then
            echo "The JSON generation process failed." >&2
        else
            # Generate the HTML
            python3 merge_html.py template.html $json_file $html_file

            # Did it fail?
            if [ $? -ne 0 ]; then
                echo "The HTML generation process failed." >&2
            fi
        fi
    fi
}