import sys
from enum import Enum
from struct import unpack
from string import Template

# Constants (Section Names)
HEADER_OFFSET = 0
HEADER_LENGTH = 96
FADER_OFFSET = HEADER_OFFSET + HEADER_LENGTH
FADER_ITEM_SIZE = 4
FADER_LENGTH = 16 * FADER_ITEM_SIZE
PAN_OFFSET = FADER_OFFSET + FADER_LENGTH
PAN_ITEM_SIZE = 4
PAN_LENGTH = 16 * PAN_ITEM_SIZE
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
FILE_NAMES = UNKNOWN2_OFFSET + UNKNOWN2_LENGTH
FILE_NAMES_ITEM_SIZE = 16
FILE_NAMES_LENGTH = 17 * FILE_NAMES_ITEM_SIZE

# Enumerations
HIGH_FREQS = Enum('HIGH_FREQS', ['500', '630', '800', '1.0k', '1.3k', '1.6k', '2.0k', '2.5k', '3.2k', '4k', '5k', '6.3k', '8k', '10k', '12.5k', '16k', '18k'], start=0)
MID_FREQS = Enum('MID_FREQS', ['40', '50', '63', '80', '100', '125', '160', '200', '250', '315', '400', '500', '630', '800', '1.0k', '1.3k', '1.6k', '2.0k', '2.5k', '3.2k', '4k', '5k', '6.3k', '8k', '10k', '12.5k', '16k', '18k'], start=0)
LO_FREQS = Enum('LO_FREQS', ['40', '50', '63', '80', '100', '125', '160', '200', '250', '315', '400', '500', '630', '800', '1.0k', '1.3k', '1.6k'], start=0)

# Helper function: Convert an offset + an index + entry size to get an address
def get_binary_address(offset, index, item_length):
    return offset + index * item_length

# Helper function: Convert binary data into a number
def convert_binary_to_int(binary_data):
    # Convert the binary data to a list of integers.
    binary_data_as_ints = [int(byte) for byte in binary_data]

    # If the length is greater than 4, complain...
    if len(binary_data_as_ints) > 4:
        print("Unexpected condition: Trying to convert more than 4 bytes to an integer.")
    else:
        return unpack('i', binary_data)[0]


# Helper function: Convert a binary range to characters
def convert_binary_to_ascii(binary_data):
    # Convert the binary data to a list of integers.
    binary_data_as_ints = [int(byte) for byte in binary_data]

    # Convert the list of integers to a string of ASCII characters.
    ascii_characters = [chr(int) for int in binary_data_as_ints]

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
    # If the integer value is hex C, then return '0db'
    if int_value == 0xC:
        return '0dB'
    elif int_value < 0xC:
        return Template('-${value}dB').substitute(value=0xc - int_value)
    else:
        return Template('+${value}dB').substitute(value=int_value - 0xc)

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

# Define a Band of EQ settings for a Track
class EQBandInfo:
    # Constructor
    def __init__(self, band, on_off, gain, freq, q_factor):
        self.band = band
        self.on_off = on_off
        self.gain_val = gain
        self.gain = get_gain_str(gain)
        self.freq_val = freq
        self.freq = get_freq_str(band, freq)
        self.q_factor_val = q_factor
        self.q_factor = get_q_factor_str(band, q_factor)

    # How to convert to a string
    def __str__(self):
        # If off, just return that...
        if not self.on_off:
            return 'off'
        elif self.band == 'mid':
            return Template('<gain=${gain}, freq=${freq}, q_factor=${q_factor}>').substitute(gain=self.gain, freq=self.freq, q_factor=self.q_factor)
        else:
            return Template('<gain=${gain}, freq=${freq}>').substitute(gain=self.gain, freq=self.freq)

# Define EQ Settings for a Track
class EQInfo:
    # Constructor
    def __init__(self, hi_band, mid_band, lo_band):
        self.hi_band = EQBandInfo('hi', hi_band[0], hi_band[3], hi_band[1], -1)
        self.mid_band = EQBandInfo('mid', mid_band[0], mid_band[3], mid_band[1], mid_band[2])
        self.lo_band = EQBandInfo('lo', lo_band[0], lo_band[3], lo_band[1], -1)

    # Convert to a string
    def __str__(self):
        return Template('[hi=$hi_band, mid=$mid_band, lo=$lo_band]').substitute(hi_band=self.hi_band, mid_band=self.mid_band, lo_band=self.lo_band)

    # Class method to construct from a ProjecFile object and track number
    @classmethod
    def extract_eq_info(cls, project_file, track_num):
        # Get the address of the EQ info
        eq_address = get_binary_address(EQ_OFFSET, track_num-1, EQ_ITEM_SIZE)

        # Extract out the fields...
        eq_fields = unpack('iiiiiiiiiiii', project_file.data[eq_address:eq_address+EQ_ITEM_SIZE])

        # Construct each of the individual fields
        hi_band_values = eq_fields[0:4]
        mid_band_values = eq_fields[4:8]
        lo_band_values = eq_fields[8:12]

        return EQInfo(hi_band_values, mid_band_values, lo_band_values)

# Define information for a single Track/File
class TrackInfo:
    # Constructor
    def __init__(self, track_num, file_name, pan, eq_info):
        self.track_num = track_num
        self.file_name = file_name
        self.track_name = file_name[0:8]
        self.pan = pan
        self.eq_info = eq_info

    # Class level method to construct from a ProjectFile object and a track number
    @classmethod
    def extract_track_info(cls, project_file, track_num):
        # Get the address of the file name
        file_name_address = get_binary_address(FILE_NAMES, track_num-1, FILE_NAMES_ITEM_SIZE)

        # Find the file name associated with the track
        file_name = convert_binary_to_ascii(project_file.data[file_name_address:file_name_address+12]) # Was: file_name_address+FILE_NAMES_ITEM_SIZE

        # Get the address of the pan value
        pan_address = get_binary_address(PAN_OFFSET, track_num-1, PAN_ITEM_SIZE)

        # Find the pan value...
        pan_value = convert_binary_to_int(project_file.data[pan_address:pan_address+PAN_ITEM_SIZE])
        pan_str = get_pan_str(pan_value)

        # Create an EQ Info section
        eq_info = EQInfo.extract_eq_info(project_file, track_num)

        return TrackInfo(track_num, file_name, pan_str, eq_info)

    # Class level

# Define our Project File class
class ProjectFile:
    # Constructor requires a binary array
    def __init__(self, binary_array):
        self.data = binary_array
        self.file_length = len(self.data)
        self.project_number = 'NIY';
        self.project_name = convert_binary_to_ascii(self.data[0x34:0x3c])

    # Get the ith Track Info
    def get_track_info(self, track_num):
        # TODO Read all tracks at startup and simply give out later...
        return TrackInfo.extract_track_info(self, track_num)

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
    if len(sys.argv[1:]) == 0:
        print("Missing project file to open...\n")
    else:
        print(Template('Processing $project_file...\n').substitute(project_file=sys.argv[1]))
        project_file = ProjectFile.open_file(sys.argv[1])
        print(Template('Found $size bytes in Project "$name".').substitute(size=project_file.file_length, name=project_file.project_name))

        # Loop through the Track Infos...
        print('\nTrack Info\n')
        for i in range(16):
            # Get the information
            track_info = project_file.get_track_info(i+1)

            # Display info
            print(Template('Track #$track_num: file_name=$file_name, track_name=$track_name, pan=$pan, eq_info=$eq_info').substitute(track_num=track_info.track_num, file_name=track_info.file_name, track_name=track_info.track_name, pan=track_info.pan, eq_info=track_info.eq_info))