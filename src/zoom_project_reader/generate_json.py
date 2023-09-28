from pathlib import Path
import re
from os import scandir, listdir
import sys
from enum import Enum
from struct import unpack
from string import Template
from itertools import takewhile
import jsons
from jsons import JsonSerializable
from util import status

# Constants (file and directory names)
PROJECT_FILE_NAME = "PRJDATA.ZDT"
EFFECTS_FILE_NAME = "EFXDATA.ZDT"
AUDIO_DIR_NAME = "AUDIO"

# ZDT FILE CONTENTS
EFFECTS_FILE_HEADER = 'ZOOM R-16  EFFECT DATA VER0001'

# Constants (Section Names)
HEADER_OFFSET = 0
HEADER_LENGTH = 96
FADER_OFFSET = HEADER_OFFSET + HEADER_LENGTH
FADER_ITEM_SIZE = 4
FADER_LENGTH = 16 * FADER_ITEM_SIZE
PAN_OFFSET = FADER_OFFSET + FADER_LENGTH
PAN_ITEM_SIZE = 4
PAN_LENGTH = 16 * PAN_ITEM_SIZE
PAN_VALUE_CENTER = 0xc
CHORUS_SEND_OFFSET = PAN_OFFSET + PAN_LENGTH
CHORUS_SEND_ITEM_SIZE = 4
CHORUS_SEND_LENGTH = 16 * CHORUS_SEND_ITEM_SIZE
REVERB_SEND_OFFSET = CHORUS_SEND_OFFSET + CHORUS_SEND_LENGTH
REVERB_SEND_ITEM_SIZE = 4
REVERB_SEND_LENGTH = 16 * REVERB_SEND_ITEM_SIZE
UNKNOWN1_OFFSET = REVERB_SEND_OFFSET + REVERB_SEND_LENGTH
UNKNOWN1_ITEM_SIZE = 4
UNKNOWN1_LENGTH = 16 * UNKNOWN1_ITEM_SIZE
EQ_OFFSET = UNKNOWN1_OFFSET + UNKNOWN1_LENGTH
EQ_ITEM_SIZE = 48
EQ_LENGTH = 16 * EQ_ITEM_SIZE
UNKNOWN2_OFFSET = EQ_OFFSET + EQ_LENGTH
UNKNOWN2_ITEM_SIZE = 1
UNKNOWN2_LENGTH = 8 * UNKNOWN2_ITEM_SIZE
FILE_NAMES_OFFSET = UNKNOWN2_OFFSET + UNKNOWN2_LENGTH
FILE_NAMES_ITEM_SIZE = 16
FILE_NAMES_LENGTH = 17 * FILE_NAMES_ITEM_SIZE
UNKNOWN3_OFFSET = FILE_NAMES_OFFSET + FILE_NAMES_LENGTH
UNKNOWN3_LENGTH = 4
CHORUS_SEND_ON_OFF_OFFSET = UNKNOWN3_OFFSET + UNKNOWN3_LENGTH
CHORUS_SEND_ON_OFF_LENGTH = 4
REVERB_SEND_ON_OFF_OFFSET = CHORUS_SEND_ON_OFF_OFFSET + CHORUS_SEND_ON_OFF_LENGTH
REVERB_SEND_ON_OFF_LENGTH = 4

# Enumerations
HIGH_FREQS = Enum('HIGH_FREQS', ['500', '630', '800', '1.0k', '1.3k', '1.6k', '2.0k', '2.5k', '3.2k', '4k', '5k', '6.3k', '8k', '10k', '12.5k', '16k', '18k'], start=0)
MID_FREQS = Enum('MID_FREQS', ['40', '50', '63', '80', '100', '125', '160', '200', '250', '315', '400', '500', '630', '800', '1.0k', '1.3k', '1.6k', '2.0k', '2.5k', '3.2k', '4k', '5k', '6.3k', '8k', '10k', '12.5k', '16k', '18k'], start=0)
LO_FREQS = Enum('LO_FREQS', ['40', '50', '63', '80', '100', '125', '160', '200', '250', '315', '400', '500', '630', '800', '1.0k', '1.3k', '1.6k'], start=0)

# Helper function: Convert an offset + an index + entry size to get an address
def get_binary_address(offset, index, item_length):
    return offset + index * item_length

# Helper function: Convert byte into an unsigned number
def convert_byte_to_int(binary_data):
    return unpack('B', binary_data)[0]

# Helper function: Convert binary data into a number
def convert_binary_to_int(binary_data):
    # If the length is greater than 4, complain...
    if len(binary_data) > 4:
        raise Exception("Unexpected condition: Trying to convert more than 4 bytes to an integer.")
    else:
        return unpack('i', binary_data)[0]

# Helper function: Convert a binary range to characters
def convert_binary_to_ascii(binary_data):
    # Loop through the binary data array until the first NULL character
    ascii_characters = (chr(int(byte)) for byte in takewhile(lambda x: x != 0, binary_data))

    return ''.join(ascii_characters)

# Get the value of PAN from a numeric representation
def get_pan_str(int_value):
    # If the integer value is 50, then return 'C'
    if int_value == 50:
        return 'C'
    elif int_value < 50:
        return Template('L$value').substitute(value=(50-int_value)*2)
    else:
        return Template('R$value').substitute(value=(int_value-50)*2)

# Get the value of GAIN from a numeric representation
def get_gain_str(int_value):
    # If the integer value is PAN CENTER, then return '0'
    if int_value == PAN_VALUE_CENTER:
        return '0'
    elif int_value < PAN_VALUE_CENTER:
        return Template('-${value}').substitute(value=PAN_VALUE_CENTER - int_value)
    else:
        return Template('+${value}').substitute(value=int_value - PAN_VALUE_CENTER)

# Get the value of the FREQ from a numeric representation (and a BAND)
def get_freq_str(band, int_value):
    # If HI Band, use HIGH_FREQS
    if band == 'hi':
        return HIGH_FREQS(int_value).name
    elif band == 'mid':
        return MID_FREQS(int_value).name
    else:
        return LO_FREQS(int_value).name

# Get the value of the Q FACTOR from a numeric representation (and a BAND)
def get_q_factor_str(band, int_value):
    # If MID band, ...
    if band == 'mid':
        return (int_value+1) / 10
    else:
        return ''

# Get the value of a bit set in a mask
def get_bitmask_value(binary_data, address, bit_pos):
    # Get the value for all 16 tracks
    bitmask = convert_binary_to_int(binary_data[address:address+4])

    # Get the bit
    return bitmask & (1 << bit_pos)

# Define a Band of EQ settings for a Track
class EQBandInfo(JsonSerializable):
    # Constructor
    def __init__(self, band, on_off, gain, freq, q_factor=-1):
        self.band:str = band
        self.on_off:bool = on_off
        self._gain_val = gain
        self.gain:str  = get_gain_str(gain)
        self._freq_val = freq
        self.freq:str = get_freq_str(band, freq)
        self._q_factor_val = q_factor
        self.q_factor:str = get_q_factor_str(band, q_factor)

    # How to convert to a string
    def __str__(self):
        # If off, just return that...
        if not self.on_off:
            return 'off'
        elif self.band == 'mid':
            return Template('<gain=${gain}, freq=${freq}, q_factor=${q_factor}>').substitute(self.__dict__)
        else:
            return Template('<gain=${gain}, freq=${freq}>').substitute(self.__dict__)

# Define EQ Settings for a Track
class EQInfo(JsonSerializable):
    # Constructor
    def __init__(self, hi_band: EQBandInfo, mid_band: EQBandInfo, lo_band: EQBandInfo):
        self.hi_band = EQBandInfo('hi', hi_band[0], hi_band[3], hi_band[1])
        self.mid_band = EQBandInfo('mid', mid_band[0], mid_band[3], mid_band[1], mid_band[2])
        self.lo_band = EQBandInfo('lo', lo_band[0], lo_band[3], lo_band[1])

    # Convert to a string
    def __str__(self):
        # Gather all of the bands that are ON
        band_info_arr = []
        for band in [self.hi_band, self.mid_band, self.lo_band]:
            if band.on_off:
                band_info_arr.append(Template('$band=$info').substitute(band=band.band, info=str(band)))

        # If there are no bands enabled, simply return off
        if len(band_info_arr) == 0:
            return "off"
        else:
            return "[" + ", ".join(band_info_arr) + "]"

    # Class method to construct from a ProjecFile object and track number
    @classmethod
    def extract_eq_info(cls, project_file, track_num):
        # Get the address of the EQ info
        eq_addr = get_binary_address(EQ_OFFSET, track_num-1, EQ_ITEM_SIZE)

        # Extract out the fields...
        eq_fields = unpack('iiiiiiiiiiii', project_file._data[eq_addr:eq_addr+EQ_ITEM_SIZE])

        # Construct each of the individual fields
        hi_band_values = eq_fields[0:4]
        mid_band_values = eq_fields[4:8]
        lo_band_values = eq_fields[8:12]

        return EQInfo(hi_band_values, mid_band_values, lo_band_values)

# Define information for a single Track/File
class TrackInfo(JsonSerializable):
    # Constructor
    def __init__(self, track_num: int, file_name: str, pan: str, eq_info: EQInfo, fader: int, reverb_send: int, reverb_send_on_off: bool, chorus_send: int, chorus_send_on_off: bool):
        self.track_num = track_num
        self.file_name = file_name
        self.track_name = file_name[0:8]
        self.pan = pan
        self.eq_info = eq_info
        self.fader = fader
        self.reverb_send = reverb_send
        self.reverb_send_on_off = reverb_send_on_off
        self.chorus_send = chorus_send
        self.chorus_send_on_off = chorus_send_on_off

    # How to display the file as a string
    def __str__(self):
        # Are we without a file name?
        if self.file_name == "":
            return ""

        # Otherwise, construct
        return Template('Track #$track_num: file_name=$file_name, track_name=$track_name, pan=$pan, eq_info=$eq_info, fader=$fader, reverb_send=$reverb_send (On=$reverb_send_on_off), chorus_send=$chorus_send (On=$chorus_send_on_off)').substitute(self.__dict__)

    # Whether a track is "used" or not
    def is_used(self):
        return self.file_name != ""

    # Class level method to construct from a ProjectFile object and a track number
    @classmethod
    def extract_track_info(cls, project_file, track_num):
        # Get the address of the file name
        file_name_addr = get_binary_address(FILE_NAMES_OFFSET, track_num-1, FILE_NAMES_ITEM_SIZE)

        # Find the file name associated with the track
        file_name = convert_binary_to_ascii(project_file._data[file_name_addr:file_name_addr+12]) # Was: file_name_addr+FILE_NAMES_ITEM_SIZE

        # Get the address of the pan value
        pan_addr = get_binary_address(PAN_OFFSET, track_num-1, PAN_ITEM_SIZE)

        # Find the pan value...
        pan_value = convert_binary_to_int(project_file._data[pan_addr:pan_addr+PAN_ITEM_SIZE])
        pan_str = get_pan_str(pan_value)

        # Create an EQ Info section
        eq_info = EQInfo.extract_eq_info(project_file, track_num)

        # Get the fader address
        fader_addr = get_binary_address(FADER_OFFSET, track_num-1, FADER_ITEM_SIZE)

        # Get the fader value
        fader = convert_binary_to_int(project_file._data[fader_addr:fader_addr+FADER_ITEM_SIZE])

        # Get the reverb send value address
        reverb_send_addr = get_binary_address(REVERB_SEND_OFFSET, track_num-1, REVERB_SEND_ITEM_SIZE)

        # Get the actual value of reverb send (regardless of whether it is ON/OFF)
        reverb_send_value = convert_binary_to_int(project_file._data[reverb_send_addr:reverb_send_addr+REVERB_SEND_ITEM_SIZE])

        # Get the bitmask value for this track
        reverb_send_on_off = get_bitmask_value(project_file._data, REVERB_SEND_ON_OFF_OFFSET, track_num-1)

        # Get the chorus send value address
        chorus_send_addr = get_binary_address(CHORUS_SEND_OFFSET, track_num-1, CHORUS_SEND_ITEM_SIZE)

        # Get the actual value of chorus send (regardless of whether it is ON/OFF)
        chorus_send_value = convert_binary_to_int(project_file._data[chorus_send_addr:chorus_send_addr+CHORUS_SEND_ITEM_SIZE])

        # Get the bitmask value for this track
        chorus_send_on_off = get_bitmask_value(project_file._data, CHORUS_SEND_ON_OFF_OFFSET, track_num-1)

        return TrackInfo(track_num, file_name, pan_str, eq_info, fader, reverb_send_value, reverb_send_on_off, chorus_send_value, chorus_send_on_off)

# Define our binary file base class
class BinaryFile():
    # Constructor requires the binary array
    def __init__(self, binary_array):
        self._data = binary_array

    # Define a class-level method to return a BinaryFile instance
    @classmethod
    def open_file(cls, file_name):
        # Open file for reading as binary...
        file_handle = open(file_name, 'rb')

        # Read the contents of the entire file
        contents = file_handle.read()

        # Close the file
        file_handle.close()

        # Return an instance of ourself
        return BinaryFile(contents)

# Define our Effects File class
class EffectsFile(BinaryFile):
    # Verify that the binary file looks correct
    @classmethod
    def verify_binary(cls, binary_data):
        # Get the header info
        header_text = convert_binary_to_ascii(binary_data[0:0+30])

        # Verify that it matches what is expected...
        if not header_text == EFFECTS_FILE_HEADER:
            raise Exception(Template('Unexpected Effects File [header_text="$header_text"]').substitute(header_text=header_text))

    # Retrieve reverb info
    def get_reverb_info(self):
        # First, determine whether the bit is sent that tells whether it is ON or OFF
        bitmask = convert_byte_to_int(self._data[0x62:0x62+1])
        reverb_on_off = bitmask & (1 << 1) == 0

        # If off, return two empty strings
        if not reverb_on_off:
            return ("", "")

        # Get the reverb patch number
        reverb_num = convert_binary_to_int(self._data[0x5c:0x5c+4])

        # Get the reverb patch name
        reverb_name = convert_binary_to_ascii(self._data[0x106:0x106+8])

        return (str(reverb_num).zfill(2), reverb_name)

    # Retrieve chorus info
    def get_chorus_info(self):
        # First, determine whether the bit is sent that tells whether it is ON or OFF
        bitmask = convert_byte_to_int(self._data[0x62:0x62+1])
        chorus_on_off = bitmask & (1 << 0) == 0

        # If off, return two empty strings
        if not chorus_on_off:
            return ("", "")

        # Get the chorus patch number
        chorus_num = convert_binary_to_int(self._data[0x58:0x58+4])

        # Get the chorus patch name
        chorus_name = convert_binary_to_ascii(self._data[0xE8:0xE8+8])

        return (str(chorus_num).zfill(2), chorus_name)

    # Class level method to return a Project from a file
    @classmethod
    def open_file(cls, file_name):
        # Load the binary data...
        binary_file = BinaryFile.open_file(file_name)

        # Verify it is correct...
        cls.verify_binary(binary_file._data)

        # Return an instance of ourself
        return EffectsFile(binary_file._data)

# Define our Project File class
class ProjectFile(BinaryFile, JsonSerializable):
    # Constructor requires a project number and a binary array
    def __init__(self, project_number, binary_array):
        # Invoke our base class constructor
        BinaryFile.__init__(self, binary_array)

        # Derive instance level attributes from the underlying binary data
        self._file_length = len(self._data)
        self.project_number:str = str(project_number).zfill(3);
        self.project_name:str = convert_binary_to_ascii(self._data[0x34:0x3c])
        self.track_info = []
        for i in range(16):
            self.track_info.append(TrackInfo.extract_track_info(self, i+1))

    # Try to find a track by a field name and value
    def find_track(self, field_name, field_value):
        # Loop through the track numbers
        for i in range(16):
            # Is this field the track number and does it match?
            if field_name == "track_num" and field_value == i:
                return(self.track_info[i])

            # Is this field the track name and does it match?
            if field_name == "track_name" and field_value == self.track_info[i].track_name:
                return self.track_info[i]

            # Is this field the file name and does it match?
            if field_name == "file_name" and field_value == self.track_info[i].file_name:
                return self.track_info[i]

    # Import extra info
    def import_extra_info(self, obj):
        # Do we have a card name?
        if obj["card_name"]:
            self.card_name = obj["card_name"]

        # Do we have a project full name?
        if obj["project_name_full"]:
            self.project_name_full = obj["project_name_full"]

        # Do we have a tracks section?
        if "tracks" in obj:
            # Loop through each track object and try to associate bars_used
            for track_name in obj["tracks"]:
                # Try to find the track by its name...
                track = self.find_track("track_name", track_name)

                # If we have a matching, track, add extra info...
                if track:
                    track.bars_used = obj["tracks"][track_name]["bars_used"]

    # Set our send effects
    def set_send_effects(self, reverb_num, reverb_name, chorus_num, chorus_name):
        self.reverb_number:str = reverb_num
        self.reverb_name:str = reverb_name
        self.chorus_number:str = chorus_num
        self.chorus_name:str = chorus_name

    # Store our our extra audio files
    def set_extra_audio_files(self, extra_audio_files):
        self.extra_audio_files:[str] = extra_audio_files

    # Class level method to return a Project from a file
    @classmethod
    def open_file(cls, project_number, file_name):
        # Load the binary data...
        binary_file = BinaryFile.open_file(file_name)

        # Return an instance of ourself
        return ProjectFile(project_number, binary_file._data)

# An exception class that indicates an invalid project directory
class InvalidProjectDirectory(Exception):
    # Constructor
    def __init__(self, dir_path, message):
        self.dir_path = dir_path
        self.message = message

# Define our Project Directory class
class ProjectDir():
    # Constructor...
    def __init__(self, project_file, effects_file, audio_files, num_files):
        self.project_file = project_file
        self.effects_file = effects_file
        self.audio_files = audio_files
        self._num_files = num_files

    # Class level method to read the contents of a project directory
    @classmethod
    def read_directory(cls, dir_path_str):
        # Get the directory entry for this path
        dir_path = Path(dir_path_str)

        # If this is not a directory, then get out now...
        if not dir_path.exists() or not dir_path.is_dir():
            raise InvalidProjectDirectory(dir_path, Template("Directory does not exist: $dir_path").substitute(dir_path=dir_path))

        # Get the directory name from the directory path
        dir_name = dir_path.name

        # Verify that the directory has an expected name
        match = re.fullmatch(r'PROJ(\d{3})', dir_name)
        if not match:
            raise InvalidProjectDirectory(dir_path, Template("Unexpected directory name: $dir_name").substitute(dir_name=dir_name))

        # Get the project number
        project_number = int(match.group(1))

        # Initialize a total count of files
        num_files = 0

        # Loop through the top-level entries...
        for dir_entry in scandir(dir_path):
            # Is this the project file?
            if dir_entry.name == PROJECT_FILE_NAME and not dir_entry.is_dir():
                # Increment the number of files traversed
                num_files += 1

                # Read the project file
                project_file = ProjectFile.open_file(project_number, dir_entry.path)
            elif dir_entry.name == EFFECTS_FILE_NAME and not dir_entry.is_dir():
                # Increment the number of files traversed
                num_files += 1

                # Read the effect file
                effects_file = EffectsFile.open_file(dir_entry.path)
            elif dir_entry.name == AUDIO_DIR_NAME and dir_entry.is_dir():
                # Read the contents of this directory in
                audio_files = listdir(dir_entry.path)

                # Increment the number of files traversed
                num_files += len(audio_files)

        # If we don't have a project file, effects file and audio files array, then complain!
        if not project_file or not effects_file or len(audio_files) == 0:
            raise InvalidProjectDirectory("Invalid project directory: missing project file, effects file or audio files!")

        # Get the reverb number and name from the effects file
        (reverb_num, reverb_name) = effects_file.get_reverb_info()

        # Get the chorus number and name from the effects file
        (chorus_num, chorus_name) = effects_file.get_chorus_info()

        # Store the reverb info in the project file
        project_file.set_send_effects(reverb_num, reverb_name, chorus_num, chorus_name)

        # Find the "extra" files that are not associated with tracks
        extra_audio_files = [audio_file for audio_file in audio_files if not project_file.find_track("file_name", audio_file)]

        # Store the extra file names with the project
        project_file.set_extra_audio_files(extra_audio_files)

        # Create an instance...
        return ProjectDir(project_file, effects_file, audio_files, num_files)

if __name__ == '__main__':
    # Look for command line argument of file name...
    if len(sys.argv[1:]) < 3:
        # Status...
        print("Missing files: PROJECT_DIR EXTRA_JSON_FILE OUTPUT_JSON_FILE")
    else:
        # Diagnostics
        status(Template('Reading $project_dir...').substitute(project_dir=sys.argv[1]))

        # Open the project directory for reading...
        try:
            # Get the Project Directory object...
            project_dir = ProjectDir.read_directory(sys.argv[1])

            # Retrieve the project file
            project_file = project_dir.project_file

            # Diagnostics
            print(Template('OK [$num_files files in Project "$name"]').substitute(num_files=project_dir._num_files, name=project_file.project_name))
        except InvalidProjectDirectory as ipd:
            # Diagnostics
            print(Template("Error [$message]").substitute(message=ipd.message))

            # Exit with a failure
            sys.exit(1)

        # Diagnostics...
        status(Template('Loading $extra_json_file...').substitute(extra_json_file=sys.argv[2]))

        # Open the extra JSON file for reading
        try:
            with open(sys.argv[2], "r") as extra_json_file:
                # Read the JSON
                extra_json_text = extra_json_file.read()

                # Convert it to a JSON object
                initial_json_obj = jsons.loads(extra_json_text)

                # Enhance class
                project_file.import_extra_info(initial_json_obj)

                print("OK")
        except FileNotFoundError as fnf:
            print(Template("Error [$message (ignored)]").substitute(message=fnf.message))

        # Open the output json file for writing
        status(Template("Opening ${output_file} for writing JSON...").substitute(output_file=sys.argv[3]))
        with open(sys.argv[3], "w") as output_file:
            # Get the JSON
            json_text = jsons.dumps(project_file, strip_privates=True)

            # Write to the file
            output_file.write(json_text)

            # Diagnostics
            print("OK");
