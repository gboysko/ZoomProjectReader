from pathlib import Path
import re
from os import scandir, listdir
import sys
from struct import unpack
from string import Template
from itertools import takewhile
import jsons
from jsons import JsonSerializable
from util import status
import zoomrlib

# Constants (file and directory names)
PROJECT_FILE_NAME = "PRJDATA.ZDT"
EFFECTS_FILE_NAME = "EFXDATA.ZDT"
AUDIO_DIR_NAME = "AUDIO"

# ZDT FILE CONTENTS
EFFECTS_FILE_HEADER = 'ZOOM R-16  EFFECT DATA VER0001'

# Helper function: Convert byte into an unsigned number
def convert_byte_to_int(binary_data):
    return unpack('B', binary_data)[0]

# Helper function: Convert binary data into a number
def convert_binary_to_int(binary_data):
    # If the length is greater than 4, complain...
    if len(binary_data) > 4:
        raise Exception("Unexpected condition: Trying to convert more than 4 bytes to an integer.")

    return unpack('i', binary_data)[0]

# Helper function: Convert a binary range to characters
def convert_binary_to_ascii(binary_data):
    # Loop through the binary data array until the first NULL character
    ascii_characters = (chr(int(byte)) for byte in takewhile(lambda x: x != 0, binary_data))

    return ''.join(ascii_characters)

# Get the value of PAN from a numeric representation
def get_pan_str(int_value):
    # If the integer value is 50, then return 'C'
    if int_value == 0:
        return 'C'

    # What is the prefix character?
    prefix = 'L' if int_value < 0 else 'R'

    return prefix + str(abs(int_value)*2)

# Get the value of GAIN from a numeric representation
def get_gain_str(int_value):
    # Is there a prefix
    prefix = '+' if int_value > 0 else ''

    return prefix + str(int_value)

# Get the value of the FREQ from a numeric representation (and a BAND)
def get_freq_str(int_value):
    # Convert to our expected format...
    if int_value < 1000:
        return str(int_value)

    # Divide by 1000
    fraction_of_kilohertz = str(int_value / 1000) + 'k'
    len_of_str = len(fraction_of_kilohertz)

    # If there is no fractional component, remove it...
    if fraction_of_kilohertz[len_of_str-3:] == '.0k' and int_value not in [1000, 2000]:
        return fraction_of_kilohertz[0:len_of_str-3] + 'k'

    return fraction_of_kilohertz

# Define a Band of EQ settings for a Track
class EQBandInfo(JsonSerializable):
    # Constructor
    def __init__(self, band, on_off, gain, freq, q_factor=-1):
        self.band:str = band
        self.on_off:bool = on_off
        self._gain_val = gain
        self.gain:str  = get_gain_str(gain)
        self._freq_val = freq
        self.freq:str = get_freq_str(freq)
        self.q_factor:str = q_factor

    # How to convert to a string
    def __str__(self):
        # If off, just return that...
        if not self.on_off:
            return 'off'

        # Is it mid-range EQ?
        if self.band == 'mid':
            return Template('<gain=${gain}, freq=${freq}, q_factor=${q_factor}>').substitute(self.__dict__)

        return Template('<gain=${gain}, freq=${freq}>').substitute(self.__dict__)

# Define EQ Settings for a Track
class EQInfo(JsonSerializable):
    # Constructor
    def __init__(self, hi_band, mid_band, lo_band):
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

        return "[" + ", ".join(band_info_arr) + "]"

# Define information for a single Track/File
class TrackInfo:
    # Constructor
    def __init__(self, track_num:int, prjdata):
        # Use the Zoom library
        tracklib = prjdata.tracks[track_num-1]

        # Is the track ON?
        track_on = tracklib.status == zoomrlib.PLAY # or tracklib.status == zoomrlib.REC

        # Is there no track name?
        no_track_name = tracklib.file[0:1] == '\x00'

        # Record our track number
        self.track_num = track_num

        # Fill in our names
        if no_track_name:
            self.file_name = ""
            self.track_name = ""
        else:
            self.file_name = tracklib.file
            self.track_name = self.file_name[0:8]

        # Construct data for our EQ Bands
        hi_band_info = [tracklib.eqhigh_on and track_on, tracklib.eqhigh_freq, 0, tracklib.eqhigh_gain]
        mid_band_info = [tracklib.eqmid_on and track_on, tracklib.eqmid_freq, tracklib.eqmid_qfactor, tracklib.eqmid_gain]
        low_band_info = [tracklib.eqlow_on and track_on, tracklib.eqlow_freq, 0, tracklib.eqlow_gain]
        self.eq_info = EQInfo(hi_band_info, mid_band_info, low_band_info)

        # Is the track on?
        if track_on:
            # Construct other fields
            self.fader = tracklib.fader
            self.reverb_send = tracklib.reverb_gain
            self.reverb_send_on_off = tracklib.reverb_on
            self.chorus_send = tracklib.chorus_gain
            self.chorus_send_on_off = tracklib.chorus_on
            self.invert_on = tracklib.invert_on
            self.stereo_on = tracklib.stereo_on
            self.pan = get_pan_str(tracklib.pan)


# Define our binary file base class
class BinaryFile():
    # Constructor requires the binary array
    def __init__(self, binary_array):
        self._data = binary_array

    # Define a class-level method to return a BinaryFile instance
    @classmethod
    def open_file(cls, file_name):
        # Open file for reading as binary...
        with open(file_name, 'rb') as file_handle:
            # Read the contents of the entire file
            contents = file_handle.read()

            # Return an instance of ourself
            return BinaryFile(contents)

# Define our Effects File class
class EffectsFile(BinaryFile):
    # Constructor
    def __init__(self, file_name):
        # Use our zoomrlib library to read the file...
        with zoomrlib.open(file_name, "r") as file:
            # Load the file
            self.efxdata = zoomrlib.effect.load(file)

            # If not a valid file, get out now!
            if not self.efxdata.valid_header:
                raise Exception(Template('Unexpected Effects File [header_text="$header_text"]').substitute(header_text=self.efxdata.header))

    # Retrieve reverb info
    def get_reverb_info(self):
        # If SEND REVERB is off, return two empty strings
        if not self.efxdata.send_reverb_on:
            return ("", "")

        # Get the reverb patch number
        reverb_num = self.efxdata.send_reverb_patch_num

        # Get the reverb patch name
        reverb_name = self.efxdata.send_reverb_patch_name

        return (str(reverb_num).zfill(2), reverb_name)

    # Retrieve chorus info
    def get_chorus_info(self):
        # If SEND CHORUS is off, return two empty strings
        if not self.efxdata.send_chorus_on:
            return ("", "")

        # Get the chorus patch number
        chorus_num = self.efxdata.send_chorus_patch_num

        # Get the chorus patch name
        chorus_name = self.efxdata.send_chorus_patch_name

        return (str(chorus_num).zfill(2), chorus_name)

# Define information about our Master track
class MasterTrack:
    # Constructor
    def __init__(self, masterlib):
        self.name = masterlib.file[0:8]
        self.file = masterlib.file
        self.fader = masterlib.fader

# Define our Profile File class
class ProjectFile:
    # Constructor
    def __init__(self, project_number, file_name):
        # Use our zoomrlib library to read the file...
        with zoomrlib.open(file_name, "r") as file:
            prjdata = zoomrlib.project.load(file)

        # Record the project number
        self.project_number:str = str(project_number).zfill(3)

        # Get the project name
        self.project_name = prjdata.name

        # Get the Tracks...
        self.track_info = []
        for i in range(16):
            self.track_info.append(TrackInfo(i+1, prjdata))

        # Master info
        self.master = MasterTrack(prjdata.master)

        # Defaults for extra info
        self.card_name = ""
        self.project_name_full = ""

        # Defaults for SEND EFFECTS
        self.reverb_number = ""
        self.reverb_name = ""
        self.chorus_number = ""
        self.chorus_name = ""

        # Defaults for extra audio files
        self.extra_audio_files:list[str] = []

    # Try to find a track by a field name and value
    def find_track(self, field_name, field_value):
        # Loop through the track numbers
        for i in range(16):
            # Is this field the track number and does it match?
            if field_name == "track_num" and field_value == i:
                return self.track_info[i]

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
        self.extra_audio_files = sorted(extra_audio_files)

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
        self.num_files = num_files

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
                project_file = ProjectFile(project_number, dir_entry.path)
            elif dir_entry.name == EFFECTS_FILE_NAME and not dir_entry.is_dir():
                # Increment the number of files traversed
                num_files += 1

                # Read the effect file
                effects_file = EffectsFile(dir_entry.path)
            elif dir_entry.name == AUDIO_DIR_NAME and dir_entry.is_dir():
                # Read the contents of this directory in
                audio_files = listdir(dir_entry.path)

                # Increment the number of files traversed
                num_files += len(audio_files)

        # If we don't have a project file, effects file and audio files array, then complain!
        if not project_file or not effects_file: # or len(audio_files) == 0:
            raise InvalidProjectDirectory(dir_path, "Invalid project directory: missing project file, effects file or audio files!")

        # Get the reverb number and name from the effects file
        (reverb_num, reverb_name) = effects_file.get_reverb_info()

        # Get the chorus number and name from the effects file
        (chorus_num, chorus_name) = effects_file.get_chorus_info()

        # Store the reverb info in the project file
        project_file.set_send_effects(reverb_num, reverb_name, chorus_num, chorus_name)

        # Find the "extra" files that are not associated with tracks
        extra_audio_files = [audio_file for audio_file in audio_files if not project_file.find_track("file_name", audio_file)]

        # Is the master file in the list?
        if project_file.master.file in extra_audio_files:
            extra_audio_files.remove(project_file.master.file)

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
            print(Template('OK [$num_files files in Project "$name"]').substitute(num_files=project_dir.num_files, name=project_file.project_name))
        except InvalidProjectDirectory as ipd:
            # Diagnostics
            print(Template("Error [$message]").substitute(message=ipd.message))

            # Exit with a failure
            sys.exit(1)

        # Diagnostics...
        status(Template('Loading $extra_json_file...').substitute(extra_json_file=sys.argv[2]))

        # Open the extra JSON file for reading
        try:
            with open(sys.argv[2], "r", encoding="utf-8") as extra_json_file:
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
        with open(sys.argv[3], "w", encoding="utf-8") as output_file:
            # Get the JSON
            json_text = jsons.dumps(project_file, strip_privates=True)

            # Write to the file
            output_file.write(json_text)

            # Diagnostics
            print("OK")
