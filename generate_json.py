import sys
from enum import Enum
from struct import unpack
from string import Template
from itertools import takewhile
import jsons
from jsons import JsonSerializable

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

# Helper function: Convert binary data into a number
def convert_binary_to_int(binary_data):
    # If the length is greater than 4, complain...
    if len(binary_data) > 4:
        print("Unexpected condition: Trying to convert more than 4 bytes to an integer.")
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

# Define our Project File class
class ProjectFile(JsonSerializable):
    # Constructor requires a binary array
    def __init__(self, binary_array):
        self._data = binary_array
        self._file_length = len(self._data)
        self.project_number:str = 'NIY';
        self.project_name:str = convert_binary_to_ascii(self._data[0x34:0x3c])
        self.track_info = []
        for i in range(16):
            self.track_info.append(TrackInfo.extract_track_info(self, i+1))

    # Import extra info
    def import_extra_info(self, obj):
        # Do we have an card name?
        if obj["card_name"]:
            self.card_name = obj["card_name"]

        # Do we have project full name?
        if obj["project_name_full"]:
            self.project_name_full = obj["project_name_full"]

    # Class level method to return a Project from a file
    @classmethod
    def open_file(cls, file_name):
        # Open file for reading as binary...
        file_handle = open(file_name, 'rb')

        # Read the contents of the entire file
        contents = file_handle.read()

        # Close the file
        file_handle.close()

        # Return an instance of ourself
        return ProjectFile(contents)


if __name__ == '__main__':
    # Look for command line argument of file name...
    if len(sys.argv[1:]) < 3:
        # Status...
        print("Missing files: PROJECT_FILE EXTRA_JSON_FILE OUTPUT_JSON_FILE")
    else:
        # Load the Project file
        sys.stdout.write(Template('Loading $project_file...').substitute(project_file=sys.argv[1]))
        project_file = ProjectFile.open_file(sys.argv[1])
        print(Template('OK [$size bytes in Project "$name"]').substitute(size=project_file._file_length, name=project_file.project_name))

        # Open the extra JSON file for reading
        sys.stdout.write(Template('Loading $extra_json_file...').substitute(extra_json_file=sys.argv[2]))
        try:
            with open(sys.argv[2], "r") as extra_json_file:
                # Read the JSON
                extra_json_text = extra_json_file.read()

                # Convert it to a JSON object
                initial_json_obj = jsons.loads(extra_json_text)

                # Enhance class
                project_file.import_extra_info(initial_json_obj)

                print("OK")
        except FileNotFoundError:
            print("Error [File not found]")

        # Open the output json file for writing
        sys.stdout.write(Template("Opening ${output_file} for writing JSON...").substitute(output_file=sys.argv[3]))
        with open(sys.argv[3], "w") as output_file:
            # Get the JSON
            json_text = jsons.dumps(project_file, strip_privates=True)

            output_file.write(json_text)
        print("OK");
