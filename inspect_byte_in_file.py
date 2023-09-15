import sys
import re

from os import access, R_OK
from os.path import isfile
from struct import unpack_from
from string import Template

# Helper function to tell if a ?? is ascii
def to_ascii(byte_arr):
    chars = [chr(int(b)) for b in byte_arr]
    return "".join(chars)

if __name__ == '__main__':
    # Initialize some variables
    files_to_process = []
    files_to_exclude = []
    excluding = False
    offset = None
    binary_length = 1
    format_str = 'B'
    file_map = {}

    # Loop through each command line argument
    for arg in sys.argv[1:]:
        # Hex Offset RE
        hex_offset_match = re.search('--offset=0x([a-fA-F0-9]+)', arg)
        dec_offset_match = re.search('--offset=([0-9]+)', arg)
        length_match = re.search('--length=([0-9]+)', arg)

        # Check on each type of argument
        if hex_offset_match is not None:
            offset = int(hex_offset_match.group(1), 16)
        elif dec_offset_match is not None:
            offset = int(dec_offset_match.group(1), 10)
        elif length_match is not None:
            binary_length = int(length_match.group(1), 10)
        elif arg == '--exclude':
            excluding = True
        elif not isfile(arg):
            print(Template('$file: Not a file').substitute(file=arg))
        elif not access(arg, R_OK):
            print(Template('$file: Not readable').substitute(file=arg))
        elif excluding:
            files_to_exclude.append(arg)
        else:
            files_to_process.append(arg)

    # If the user has not supplied an offset, complain and return!
    if offset is None:
        print("Missing offset into file. Use --offset=HEX or --offset=DEC.")
        sys.exit(1)

    # Loop through the files to process
    for binary_file in files_to_process:
        # Is this file in the list of files to exclude?
        if binary_file in files_to_exclude:
            print(Template('$file: Excluding...').substitute(file=binary_file))
        else:
            # Open the file for reading...
            with open(binary_file, 'rb') as file_handle:
                # Read the contents of the entire file
                contents = file_handle.read()

                # Find the value of a given offset...
                # value = unpack_from(format_str, buffer=contents, offset=offset)[0]
                try:
                    value = contents[offset:offset+binary_length]
                except Exception:
                    value = "UNKNOWN"

                # Get the value as a hex string
                hex_value = bytes.hex(value)

                # Status
                print(Template('$file: Byte at Offset $offset: 0x$value').substitute(file=binary_file, offset=hex(offset), value=hex_value))

                # Use this value as a key to group the files that have this value
                if not hex_value in file_map:
                    file_map[hex_value] = []
                file_map[hex_value].append(binary_file)

    # Are there no files to process?
    if len(file_map) == 0:
        # No files to process. Show usage
        print('No files processed.')
        print(Template('$program FILE1 ... FILEn --exclude EXFILE1 ... EXFILEn'))
    else:
        # Display offset selected...
        print(Template('\nValues at File Offset $offset:').substitute(offset=hex(offset)))

        # Loop through each entry in the dictionary
        for value, arr in file_map.items():
            # Get the bytes array
            bytes_arr = bytes.fromhex(value)

            # Get the integer value
            int_value = int.from_bytes(bytes_arr, byteorder='big')

            # Display the value
            print(Template('\nValue: 0x$value ($num_files file$s)').substitute(value=value, num_files=len(arr), s='s' if len(arr) > 1 else ''))
            # print(Template('\nValue: 0x$value (asc="$bytes")').substitute(value=value, bytes=to_ascii(bytes_arr)))

            # Loop through the files
            for file in arr:
                print(Template(' * $file').substitute(file=file))
