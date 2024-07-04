# placeholder for configuration settings used by the runtime. 
# this may be replaced or retooled in future versions

# the name of the Python file and, incidentally, the name of the script in Fusion 360
LABEL_SCRIPT_NAME = "gridfinity_label_autogen"

DEBUG_MODE = False

TEMP_DIR = "C:\\Temp\\"
DEBUG_DIR = "".join([TEMP_DIR, ".debug\\"])

# logging
LOG_DIR = DEBUG_DIR if DEBUG_MODE else TEMP_DIR
LOG_FORMAT = "%(name)s : %(levelname)s : %(message)s"