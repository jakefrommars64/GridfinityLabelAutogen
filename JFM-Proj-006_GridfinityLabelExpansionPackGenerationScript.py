# Author-jakefrommars64
# Description-

# the name of the Python file and, incidentally, the name of the script in Fusion 360
_script_name_ = "jfm64_gridfinity_label_autogen_v5_1"

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, IntEnum, StrEnum
import math
import threading
import time
from types import NoneType
from typing import Callable, Optional, Union
from adsk.core import Application
import adsk.core
import adsk.fusion
import traceback

import logging
import os
import shutil

DEBUG_MODE = False

        
# Timer class
class TimerError(Exception):
    """A custom exception used to report errors in use of Timer class."""
    

class Timer:
    """create a master timer object that holds child-timers.
    Inspiration from codetiming: https://github.com/realpython/codetiming/tree/main"""
    class timer:
        """a child timer object."""
        def __init__(self, logger=None, name=None, start_time=None):
            self.logger = logger
            self.name = name
            self._start_time = start_time
            self.last = None
            
        def __repr__(self) -> str:
            return f"{self.__class__.__name__}(name={self.name}, logger={self.logger}, start_time={self._start_time}, last={self.last})"
            
    def get_formatted_time(self, name: Optional[str]=None, format: Optional[str]=None):
        if not format:
            format = self._time_format
        if name:
            return time.strftime(format, time.gmtime(self._timers[name].last))
        else:
            return time.strftime(format, time.gmtime(self.last))
        
    def make_formatted_time(self, seconds: float, format=None):
        if not format:
            format = self._time_format
        return time.strftime(format, time.gmtime(seconds))
    
    def __init__(self, logger=print, time_frmt="%m-%Y-%d %Hh:%Mm:%Ss"):
        self.logger = logger
        self._start_time = None
        self.last = None
        self._timers = {}
        self._time_format = time_frmt
    
    def start(self, name=None) -> None:
        """Start the timer."""
        # if self._start_time is not None:
        #     raise TimerError("Timer is running. Use .stop() to stop it")
        
        # log when timer starts
        if self.logger:
            if name:
                self.logger("Timer {name} started...".format(name=name))
            else:
                self.logger("Timer started...")
                
        self._start_time = time.perf_counter()
        if name:
            self._timers[name] = Timer.timer(logger=self.logger, name=name, start_time=time.perf_counter())
        
    def stop(self, name=None) -> float:
        """Stop the timer and report the elapsed time."""
        if self._start_time is None:
            raise TimerError("Timer is not running. Use .start() to start it")
        
        # calculate elapsed time
        self.last = time.perf_counter() - self._start_time
            
        if name:
            self._timers[name].last = time.perf_counter() - self._timers[name]._start_time
        
        # report elapsed time
        if self.logger:
            if name:
                self.logger("Timer {name} reported elapsed time: {sec}".format(name=name, sec=self.last))
            else:
                self.logger("Timer reported elapsed time: {sec}".format(sec=self._timers[name].last))
        
        return self.last


folder_temp = "C:\\Temp\\"
folder_debug = "".join([folder_temp, ".debug\\"])

# Set up the loggers

log_folder = folder_debug if DEBUG_MODE else folder_temp
formatter2 = logging.Formatter(fmt="%(name)s : %(levelname)s : %(message)s")
fileHandler2 = logging.FileHandler(filename=''.join([log_folder, 'debug_', datetime.now().strftime("%d-%m-%Y-%H-%M-%S"), '.log']), mode="w")
fileHandler2.setLevel(logging.DEBUG)
fileHandler2.setFormatter(fmt=formatter2)

logProg = logging.getLogger("ProgressLogger")
logProg.setLevel(logging.DEBUG)
logProg.addHandler(fileHandler2)
logProg.info("Progress Logger initiated.")

# define global app and document variables
_app = adsk.core.Application.cast(None)
_ui = adsk.core.UserInterface.cast(None)
_design = adsk.fusion.Design.cast(None)
_cmdDef = adsk.core.CommandDefinition.cast(None)

_progressDialog = adsk.core.ProgressDialog.cast(None)

# Global autogen parameters
_rootFolderName = adsk.core.StringValueCommandInput.cast(None)
_generationAlgorithm = adsk.core.DropDownCommandInput.cast(None)

# Screws, Nuts, Washers autogen parameters
_screwBoltNutWasher_lengthDependentLabel = adsk.core.BoolValueCommandInput.cast(None)
_screwBoltNutWasher_minimumLength = adsk.core.IntegerSpinnerCommandInput.cast(None)
_screwBoltNutWasher_maximumLength = adsk.core.IntegerSpinnerCommandInput.cast(None)
_screwBoltNutWasher_minimumModul = adsk.core.IntegerSpinnerCommandInput.cast(None)
_screwBoltNutWasher_maximumModul = adsk.core.IntegerSpinnerCommandInput.cast(None)

# Bearings autogen parameters
# Source: https://www.bearingworks.com/bearing-sizes/
_metricBearingDefinitions = {
    '600_series' : ['603','604','605','606','607',
                    '608','609','623','624','625',
                    '626','627','628','629','633',
                    '634','635','636','637','638',
                    '639','673','674','675','676',
                    '677','678','683','684','685',
                    '686','687','688','689','693',
                    '694','695','696','697','698','699'],
}

# Global autogen parameters
_screwBoltNutWasher_minimumBinSpan = adsk.core.IntegerSpinnerCommandInput.cast(None)
_screwBoltNutWasher_maximumBinSpan = adsk.core.IntegerSpinnerCommandInput.cast(None)
_overwriteExistingFiles = adsk.core.BoolValueCommandInput.cast(None)
_errMessage = adsk.core.TextBoxCommandInput.cast(None)

processTimerStart = time.perf_counter()
timerClassTestTimer = Timer(logger=Application.log, time_frmt="%m-%Y::%d days:%Hh:%Mm:%Ss")


# Global set of event handlers to keep them referenced for the duration of the command
_handlers = []


# Timer names
class TimerNames(Enum):
    ProcessTimer = 'process_timer'
    AutogenerationLoopTimer = 'autogeneration_loop_timer'
    generationStartTime = 'generation_start_time'
    lastGenerationTime = 'last_generation_time'


# Design parameters
# define a class that will hold the parameters from the design and make them easier to work with down the road
class DesignParameter:
    def __init__(self, name: str, design: adsk.fusion.Design):
        self.name = name
        self.parameter = design.allParameters.itemByName(self.name)
        if not self.parameter:
            self.exists = False
        else:
            self.value = self.parameter.value
            self.exists = True


# Default values for each command input
class CommandInputDefaults(IntEnum):
    MINIMUM_LENGTH = 4
    MAXIMUM_LENGTH = 6
    MINIMUM_MODUL = 1
    MAXIMUM_MODUL = 2
    MINIMUM_BIN_SPAN = 1
    MAXIMUM_BIN_SPAN = 2


class CommandInputId(StrEnum):
    ROOT_FOLDER_NAME = "input_rootFolderName"
    LENGTH_DEPENDENT_LABEL = "input_lengthDependentLabel"
    MINIMUM_LENGTH = "input_minimumLength"
    MAXIMUM_LENGTH = "input_maximumLength"
    MINIMUM_MODUL = "input_minimumModul"
    MAXIMUM_MODUL = "input_maximumModul"
    MINIMUM_BIN_SPAN = "input_minimumBinSpan"
    MAXIMUM_BIN_SPAN = "input_maximumBinSpan"
    OVERWRITE_EXISTING_FILES = "input_overwriteExistingFiles"
    GENERATION_ALGORITHM = "input_generationAlgorithm"


# ID strings for design attributes
class DesignAttributeId(StrEnum):
    # Group Names
    GROUP_SCRIPT_NAME = _script_name_

    # Item Names
    STANDARD = "standard"
    RELOAD_ATTRIBUTES = "reloadAttributes"
    ROOT_FOLDER_NAME = "rootFolderName"
    
    SBNW_LENGTH_DEPENDENT_LABEL = "lengthDependentLabel"
    SBNW_MINIMUM_LENGTH = "minimumLength"
    SBNW_MAXIMUM_LENGTH = "maximumLength"
    SBNW_MINIMUM_MODUL = "minimumModul"
    SBNW_MAXIMUM_MODUL = "maximumModul"
    SBNW_MINIMUM_BIN_SPAN = "minimumBinSpan"
    SBNW_MAXIMUM_BIN_SPAN = "maximumBinSpan"
        
    OVERWRITE_EXISTING_FILES = "overwriteExistingFiles"
    FOLDER_TEMP = "folderTemp"
    FOLDER_DEBUG = "folderDebug"


# File and variant operation types and their respective messages.
class ProgressDialogString():
    @staticmethod
    def getUpdatedMessage(currentVariation="", currentOperation="", operationTarget="", elapsedTime="", remainingTime="", averageTime=""):
        strWidth = 200
        lines = []
        lines.append("Percentage: %p %".ljust(strWidth) + "\n")
        lines.append("Elapsed Time: {elapTime}".ljust(strWidth) + "\n")
        lines.append("Remaining Time: {remainTime}".ljust(strWidth) + "\n")
        lines.append("Average Generation Time: {avgTime}".ljust(strWidth) + "\n")
        lines.append("%v / %m".ljust(strWidth) + "\n")
        lines.append("Current Variation: {curVar}".ljust(strWidth) + "\n")
        lines.append("Current Operation: {curOp}".ljust(strWidth) + "\n")
        lines.append("Operation Target: {opTar}".ljust(strWidth) + "\n")
        message = "".join(lines)
        message = message.format(
            curVar=currentVariation,
            curOp=currentOperation,
            opTar=operationTarget,
            elapTime=elapsedTime,
            remainTime=remainingTime,
            avgTime=averageTime
        )
        return message

    class OperationType(StrEnum):
        CREATE_VARIANT = "Creating Variant"
        CHECK_VARIANT_EXISTS = "Checking If Variant Exists"
        VARIANT_CREATED = "Variant Created Successfully"
        VARIANT_EXISTS = "Variant Exists : Skipping"
        CREATING_ARCHIVE = "Creating Archive"
        ARCHIVE_EXISTS = "Archive exists : Skipping"
        # DELETING_ARCHIVE_SOURCE_FOLDER = "Deleting Archive Source Folder"
        



def on_exception():
    global _ui, logProg
    e = "Failed:\n{}".format(traceback.format_exc())
    logProg.critical(e)
    if _ui:
        _ui.messageBox(e)
    adsk.terminate()


def on_terminate(canceled=False, message=None):
    try: 
        global _ui, _cmdDef, _progressDialog

        if canceled:
            message = "Canceled by user."
        else:
            if message:
                message = message
            else:
                message = "Finished"
            if _progressDialog:
                _progressDialog.hide()

        # Close the progress dialog.
        _ui.messageBox(message)

        logProg.info("JOB FINISHED. TERMINATING...")

        # Stop the command definition.
        logProg.debug("Stopping the command definition...")
        if not _cmdDef:
            _cmdDef = _ui.commandDefinitions.itemById(
                DesignAttributeId.GROUP_SCRIPT_NAME
            )

        if _cmdDef:
            _cmdDef.deleteMe()
            logProg.debug("Command Definition successfully deleted.")
            
        timerClassTestTimer.stop(name=TimerNames.ProcessTimer.value)

        logProg.debug("Shutting down logging...")
        logging.shutdown()

    except:
        on_exception()
        return


def run(context):
    try:
        global _progressDialog, folder_temp, formatter2, fileHandler2, logProg, _app, _ui, _design, _cmdDef
        global _progressDialog, _rootFolderName, _screwBoltNutWasher_lengthDependentLabel, _screwBoltNutWasher_minimumLength, _screwBoltNutWasher_maximumLength
        global _screwBoltNutWasher_minimumModul, _screwBoltNutWasher_maximumModul, _screwBoltNutWasher_minimumBinSpan, _screwBoltNutWasher_maximumBinSpan, _overwriteExistingFiles, _errMessage
        global _handlers, processTimerStart
        
        timerClassTestTimer.start(name=TimerNames.ProcessTimer.value)
        
        _app = adsk.core.Application.get()
        _ui = _app.userInterface
        _design = adsk.fusion.Design.cast(_app.activeProduct)

        attribs = _design.attributes
        attribs.add(
            DesignAttributeId.GROUP_SCRIPT_NAME,
            DesignAttributeId.FOLDER_TEMP,
            folder_temp,
        )
        attribs.add(
            DesignAttributeId.GROUP_SCRIPT_NAME,
            DesignAttributeId.FOLDER_DEBUG,
            folder_debug,
        )

        # Get the existing command definition or create it if it doesn't already exist.
        _cmdDef = _ui.commandDefinitions.itemById(DesignAttributeId.GROUP_SCRIPT_NAME)
        if not _cmdDef: 
            _cmdDef = _ui.commandDefinitions.addButtonDefinition(
                DesignAttributeId.GROUP_SCRIPT_NAME,
                "Autogenerate Gridfinity Label Variations",
                "",
                "",
            )

        # Connect to the command created event.
        onCommandCreated = MyCommandCreatedHandler()
        _cmdDef.commandCreated.add(onCommandCreated)
        _handlers.append(onCommandCreated)

        # Execute the command definition.
        _cmdDef.execute()

        # Prevent this module from being terminated when the script returns, because we are waiting for event handlers to fire.
        adsk.autoTerminate(False)

    except:
        on_exception()
        return


# Event handler that reacts to when the command is destroyed. This terminates the script.
class MyCommandDestroyHandler(adsk.core.CommandEventHandler):
    def __init__(self):
        super().__init__()

    def notify(self, args):
        try:
            # When the command is done, terminate the script
            # on_terminate()
            # This will release all globals which will remove all event handlers
            _app.log("Command Destroy handler called")
            adsk.terminate()
        except:
            on_exception()
            return


# Event handler that reacts when the command definitio is executed which
# results in the command being created and this event being fired.
class MyCommandCreatedHandler(adsk.core.CommandCreatedEventHandler):
    def __init__(self):
        super().__init__()

    def notify(self, args):
        try:
            global _progressDialog, folder_temp, formatter2, fileHandler2, logProg, _app, _ui, _design, _cmdDef
            global _progressDialog, _rootFolderName, _screwBoltNutWasher_lengthDependentLabel, _screwBoltNutWasher_minimumLength, _screwBoltNutWasher_maximumLength
            global _screwBoltNutWasher_minimumModul, _screwBoltNutWasher_maximumModul, _screwBoltNutWasher_minimumBinSpan, _screwBoltNutWasher_maximumBinSpan, _overwriteExistingFiles, _errMessage
            global _handlers, _generationAlgorithm
            eventArgs = adsk.core.CommandCreatedEventArgs.cast(args)

            if not _design:
                _ui.messageBox(
                    "A Fusion design must be active when invoking this command."
                )
                return ()

            _cmd = eventArgs.command
            _cmd.isExecutedWhenPreEmpted = False
            inputs = _cmd.commandInputs

            # Define the command dialog

            _rootFolderName = inputs.addStringValueInput(
                CommandInputId.ROOT_FOLDER_NAME, "Root folder name", ""
            )
            
            _generationAlgorithm = inputs.addDropDownCommandInput(
                CommandInputId.GENERATION_ALGORITHM,
                CommandInputId.GENERATION_ALGORITHM,
                adsk.core.DropDownStyles.TextListDropDownStyle # type: ignore
            )
            
            _screwBoltNutWasher_lengthDependentLabel = inputs.addBoolValueInput(
                CommandInputId.LENGTH_DEPENDENT_LABEL, "Length dependent label?", True
            )
            _screwBoltNutWasher_minimumLength = inputs.addIntegerSpinnerCommandInput(
                CommandInputId.MINIMUM_LENGTH,
                CommandInputId.MINIMUM_LENGTH,
                1,
                1000,
                1,
                CommandInputDefaults.MINIMUM_LENGTH,
            )
            _screwBoltNutWasher_minimumLength.isVisible = False
            _screwBoltNutWasher_maximumLength = inputs.addIntegerSpinnerCommandInput(
                CommandInputId.MAXIMUM_LENGTH,
                CommandInputId.MAXIMUM_LENGTH,
                1,
                1000,
                1,
                CommandInputDefaults.MAXIMUM_LENGTH,
            )
            _screwBoltNutWasher_maximumLength.isVisible = False
            _screwBoltNutWasher_minimumModul = inputs.addIntegerSpinnerCommandInput(
                CommandInputId.MINIMUM_MODUL,
                CommandInputId.MINIMUM_MODUL,
                1,
                50,
                1,
                CommandInputDefaults.MINIMUM_MODUL,
            )
            _screwBoltNutWasher_maximumModul = inputs.addIntegerSpinnerCommandInput(
                CommandInputId.MAXIMUM_MODUL,
                CommandInputId.MAXIMUM_MODUL,
                1,
                50,
                1,
                CommandInputDefaults.MAXIMUM_MODUL,
            )
            _screwBoltNutWasher_minimumBinSpan = inputs.addIntegerSpinnerCommandInput(
                CommandInputId.MINIMUM_BIN_SPAN,
                CommandInputId.MINIMUM_BIN_SPAN,
                1,
                50,
                1,
                CommandInputDefaults.MINIMUM_BIN_SPAN,
            )
            _screwBoltNutWasher_maximumBinSpan = inputs.addIntegerSpinnerCommandInput(
                CommandInputId.MAXIMUM_BIN_SPAN,
                CommandInputId.MAXIMUM_BIN_SPAN,
                1,
                50,
                1,
                CommandInputDefaults.MAXIMUM_BIN_SPAN,
            )
            _overwriteExistingFiles = inputs.addBoolValueInput(
                CommandInputId.OVERWRITE_EXISTING_FILES,
                "Overwrite existing files?",
                True,
            )
            _errMessage = inputs.addTextBoxCommandInput("errMessage", "", "", 2, True)
            _errMessage.isFullWidth = True

            # Connect to the command related events.
            onExecute = MyCommandExecuteHandler()
            _cmd.execute.add(onExecute)
            _handlers.append(onExecute)

            onInputChanged = MyCommandInputChangedHandler()
            _cmd.inputChanged.add(onInputChanged)
            _handlers.append(onInputChanged)

            onValidateInputs = MyCommandValidateInputsHandler()
            _cmd.validateInputs.add(onValidateInputs)
            _handlers.append(onValidateInputs)

            onDestroy = MyCommandDestroyHandler()
            _cmd.destroy.add(onDestroy)
            _handlers.append(onDestroy)

        except:
            on_exception()
            return

        
def executeScrewBoltNutWasher(args):
    global _progressDialog, folder_temp, formatter2, fileHandler2, logProg, _app, _ui, _design, _cmdDef
    global _progressDialog, _rootFolderName, _screwBoltNutWasher_lengthDependentLabel, _screwBoltNutWasher_minimumLength, _screwBoltNutWasher_maximumLength
    global _screwBoltNutWasher_minimumModul, _screwBoltNutWasher_maximumModul, _screwBoltNutWasher_minimumBinSpan, _screwBoltNutWasher_maximumBinSpan
    global _overwriteExistingFiles, _errMessage
    global _handlers, processTimerStart
    eventArgs = adsk.core.CommandEventArgs.cast(args)

    # Save the current values as attributes
    attribs = _design.attributes
    logProg.warn(''.join(['Saving current command parameters to design attributes...']))
    attribs.add(
        DesignAttributeId.GROUP_SCRIPT_NAME,
        DesignAttributeId.ROOT_FOLDER_NAME,
        _rootFolderName.value,
    )
    attribs.add(
        DesignAttributeId.GROUP_SCRIPT_NAME,
        DesignAttributeId.SBNW_LENGTH_DEPENDENT_LABEL,
        str(_screwBoltNutWasher_lengthDependentLabel.value),
    )
    attribs.add(
        DesignAttributeId.GROUP_SCRIPT_NAME,
        DesignAttributeId.SBNW_MINIMUM_LENGTH,
        str(_screwBoltNutWasher_minimumLength.value),
    )
    attribs.add(
        DesignAttributeId.GROUP_SCRIPT_NAME,
        DesignAttributeId.SBNW_MAXIMUM_LENGTH,
        str(_screwBoltNutWasher_maximumLength.value),
    )
    attribs.add(
        DesignAttributeId.GROUP_SCRIPT_NAME,
        DesignAttributeId.SBNW_MINIMUM_MODUL,
        str(_screwBoltNutWasher_minimumModul.value),
    )
    attribs.add(
        DesignAttributeId.GROUP_SCRIPT_NAME,
        DesignAttributeId.SBNW_MAXIMUM_MODUL,
        str(_screwBoltNutWasher_maximumModul.value),
    )
    attribs.add(
        DesignAttributeId.GROUP_SCRIPT_NAME,
        DesignAttributeId.SBNW_MINIMUM_BIN_SPAN,
        str(_screwBoltNutWasher_minimumBinSpan.value),
    )
    attribs.add(
        DesignAttributeId.GROUP_SCRIPT_NAME,
        DesignAttributeId.SBNW_MAXIMUM_BIN_SPAN,
        str(_screwBoltNutWasher_maximumBinSpan.value),
    )
    attribs.add(
        DesignAttributeId.GROUP_SCRIPT_NAME,
        DesignAttributeId.OVERWRITE_EXISTING_FILES,
        str(_overwriteExistingFiles.value),
    )

    # Get the current values
    rootFolderName = attribs.itemByName(
        DesignAttributeId.GROUP_SCRIPT_NAME,
        DesignAttributeId.ROOT_FOLDER_NAME).value
    lengthDependentLabel = True if attribs.itemByName(
        DesignAttributeId.GROUP_SCRIPT_NAME,
        DesignAttributeId.SBNW_LENGTH_DEPENDENT_LABEL).value == "True" else False
    minimumLength = int(attribs.itemByName(
        DesignAttributeId.GROUP_SCRIPT_NAME,
        DesignAttributeId.SBNW_MINIMUM_LENGTH).value)
    maximumLength = int(attribs.itemByName(
        DesignAttributeId.GROUP_SCRIPT_NAME,
        DesignAttributeId.SBNW_MAXIMUM_LENGTH).value)
    minimumModul = int(attribs.itemByName(
        DesignAttributeId.GROUP_SCRIPT_NAME,
        DesignAttributeId.SBNW_MINIMUM_MODUL).value)
    maximumModul = int(attribs.itemByName(
        DesignAttributeId.GROUP_SCRIPT_NAME,
        DesignAttributeId.SBNW_MAXIMUM_MODUL).value)
    minimumBinSpan = int(attribs.itemByName(
        DesignAttributeId.GROUP_SCRIPT_NAME,
        DesignAttributeId.SBNW_MINIMUM_BIN_SPAN).value)
    maximumBinSpan = int(attribs.itemByName(
        DesignAttributeId.GROUP_SCRIPT_NAME,
        DesignAttributeId.SBNW_MAXIMUM_BIN_SPAN).value)
    overwriteExistingFiles = True if attribs.itemByName(
        DesignAttributeId.GROUP_SCRIPT_NAME,
        DesignAttributeId.OVERWRITE_EXISTING_FILES
        ).value == "True" else False
    
    logProg.warn('Get operation parameter values...')
    logProg.warn(''.join(['rootFolderName = ', str(rootFolderName)]))
    logProg.warn(''.join(['lengthDependentLabel = ', str(lengthDependentLabel)]))
    logProg.warn(''.join(['minimumLength = ', str(minimumLength)]))
    logProg.warn(''.join(['maximumLength = ', str(maximumLength)]))
    logProg.warn(''.join(['minimumModul = ', str(minimumModul)]))
    logProg.warn(''.join(['maximumModul = ', str(maximumModul)]))
    logProg.warn(''.join(['minimumBinSpan = ', str(minimumBinSpan)]))
    logProg.warn(''.join(['maximumBinSpan = ', str(maximumBinSpan)]))
    logProg.warn(''.join(['overwriteExistingFiles = ', str(overwriteExistingFiles)]))

    # Create temp and debug folders if necessary
    if not os.path.isdir(folder_temp):
        os.makedirs(folder_temp)
    if not os.path.isdir(folder_debug):
        os.makedirs(folder_debug)

    if DEBUG_MODE:
        folder_root = "".join(
            [
                _design.attributes.itemByName(
                    DesignAttributeId.GROUP_SCRIPT_NAME,
                    DesignAttributeId.FOLDER_DEBUG,
                ).value,
                rootFolderName,
            ]
        )
    else:
        folder_root = "".join(
            [
                _design.attributes.itemByName(
                    DesignAttributeId.GROUP_SCRIPT_NAME,
                    DesignAttributeId.FOLDER_TEMP,
                ).value,
                rootFolderName,
            ]
        )

    totalSteps = int(
        (maximumModul + 1 - minimumModul)
        * (maximumBinSpan + 1 - minimumBinSpan)
        * (maximumLength + 1 - minimumLength)
    )

    """
    Run main logic of script.
    """
    timerClassTestTimer.start(name=TimerNames.AutogenerationLoopTimer.value)

    # Get the root component of the active design
    root_component = _design.rootComponent

    # Get parameters from the document
    param_m = DesignParameter(name="M", design=_design)
    param_bolt_length = DesignParameter(name="bolt_length_l", design=_design)
    param_bin_span = DesignParameter(name="Box_width", design=_design)
    param_label_text = DesignParameter(name="label_text", design=_design)
    param_text_height = DesignParameter(name="text_height", design=_design)
    for param in [
        param_m,
        param_bolt_length,
        param_bin_span,
        param_label_text,
        param_text_height,
    ]:
        if not param.exists:
            on_terminate(False, "Document is missing parameter " + param.name)
            return

    # Setup the progress dialog.
    _progressDialog = _ui.createProgressDialog()
    _progressDialog.cancelButtonText = "Cancel"
    _progressDialog.isBackgroundTranslucent = False
    _progressDialog.isCancelButtonShown = True
    _progressDialog.show(
        "Autogeneration in progress...",
        ProgressDialogString.getUpdatedMessage(), 
        0,
        totalSteps,
        0,
    )
    # Begin the loop for the Modul
    new_folder_span = ""
    new_folder_m = ""

    # generationStartTime = time.perf_counter()
    # lastGenerationTime = time.perf_counter() - generationStartTime
    generationStartTime = time.perf_counter()
    lastGenerationTime = 0.0
    averageGenerationTime = 0.0
    remainingSteps = _progressDialog.maximumValue
    estimatedRemainingTime = 0.0
    count = 1
    
    if lengthDependentLabel:
        
        for M in range(minimumModul, maximumModul + 1):
            # Begin the loop for Bin Span
            for bin_span in range(minimumBinSpan, maximumBinSpan + 1):
                # Begin the loop for part length
                for length in range(minimumLength, maximumLength + 1):
                    if _progressDialog.wasCancelled:
                        on_terminate(canceled=True)
                        return

                    if length % 2 == 0 or length % 5 == 0:
                        # Create the variant_name
                        variant_name = "".join(
                            [str(bin_span), "_span_M", str(M), "x", str(length)]
                        )

                        logProg.info(
                            "".join(["Creating variant '", variant_name, "'..."])
                        )

                        # Construct the modul directory
                        new_folder_m = "".join([folder_root, "\\M", str(M)])
                        logProg.info("".join(["new_folder_m = ", new_folder_m]))
                        logProg.info(
                            "".join(["Making directory '", new_folder_m, "'"])
                        )
                        if overwriteExistingFiles or not os.path.isdir(
                            new_folder_m
                        ):
                            os.makedirs(new_folder_m, exist_ok=True)
                            logProg.info("...DONE")
                        else:
                            logProg.info("...Directory already exists.")

                        # If lengthDependentLabel then construct the span directory
                        new_folder_span = "".join(
                            [new_folder_m, "\\", str(bin_span), "_span"]
                        )
                        logProg.info(
                            "".join(["new_folder_span = ", new_folder_span])
                        )
                        logProg.info(
                            "".join(
                                ["Making directory '", new_folder_span, "'"]
                            )
                        )
                        if overwriteExistingFiles or not os.path.isdir(
                            new_folder_span
                        ):
                            os.makedirs(new_folder_span, exist_ok=True)
                            logProg.info("...DONE")
                        else:
                            logProg.info("...Directory already exists.")

                        # Checking for and creating the .stl file for the variant
                        filename = "".join(
                            [new_folder_span, "\\", variant_name, ".stl"]
                        )

                        logProg.info("".join(["Filename='", filename, "'"]))
                        logProg.info("Checking if file already exists...")

                        if not overwriteExistingFiles and os.path.isfile(filename):
                            logProg.info("...File already exists. Skipping.")
                        else:
                            timerClassTestTimer.start(name=TimerNames.lastGenerationTime.value)
                            _progressDialog.message = ProgressDialogString.getUpdatedMessage(
                                currentVariation=variant_name,
                                currentOperation=ProgressDialogString.OperationType.CREATE_VARIANT,
                                operationTarget=filename,
                                elapsedTime=str((timerClassTestTimer.make_formatted_time(time.perf_counter() - generationStartTime)).split('::')[1]),
                                remainingTime=str((timerClassTestTimer.make_formatted_time(seconds=estimatedRemainingTime)).split('::')[1]),
                                averageTime=str((timerClassTestTimer.make_formatted_time(averageGenerationTime)).split('::')[1])
                            )

                            # Create the variant
                            logProg.warn(''.join(['Creating variant: ', variant_name]))
                            logProg.info(
                                "Setting Fusion 360 document parameters...."
                            )
                            param_bin_span.parameter.expression = str(bin_span)
                            param_m.parameter.expression = str(M)
                            param_label_text.parameter.comment = "".join(
                                ["M", str(M)]
                            )
                            param_bolt_length.parameter.expression = str(length)
                            param_label_text.parameter.comment = "".join(
                                [
                                    param_label_text.parameter.comment,
                                    "x",
                                    str(length),
                                ]
                            )
                            logProg.info("...DONE")
                            logProg.debug(
                                "param_text_height.value prior to firing custom event: "
                                + str(param_text_height.value)
                            )

                            logProg.info("Firing custom events...")
                            _app.fireCustomEvent(
                                "thomasa88_ParametricText_Ext_Update"
                            )
                            adsk.doEvents()
                            adsk.doEvents()
                            logProg.info("...DONE")
                            logProg.debug(
                                "param_text_height after firing custom event: "
                                + str(param_text_height.value)
                            )
                            param_text_height.parameter.expression = "4mm"
                            logProg.debug(
                                "param_text_height after updating expression: "
                                + str(param_text_height.value)
                            )

                            # Save the file as an stl
                            logProg.info(
                                "".join(
                                    ["Exporting variant '", variant_name, "'..."]
                                )
                            )
                            exportMgr = adsk.fusion.ExportManager.cast(
                                _design.exportManager
                            )
                            stlOptions = exportMgr.createSTLExportOptions(
                                root_component
                            )
                            stlOptions.meshRefinement = adsk.fusion.MeshRefinementSettings.MeshRefinementMedium  # type: ignore
                            stlOptions.filename = filename
                            exportMgr.execute(stlOptions)
                            logProg.info("...DONE")

                            # Save a screenshot
                            if length == minimumLength or length == maximumLength:
                                logProg.info(
                                    "".join(
                                        [
                                            "Saving screenshot of variant '",
                                            variant_name,
                                            "'...",
                                        ]
                                    )
                                )
                                screenshot_filename = "".join(
                                    [
                                        folder_root,
                                        "\\_screenshots\\",
                                        variant_name,
                                        ".jpg",
                                    ]
                                )
                                _app.activeViewport.goHome(False)
                                _app.activeViewport.saveAsImageFile(
                                    screenshot_filename, 800, 500
                                )
                                logProg.info("...DONE")
                            count += 1
                            lastGenerationTime = timerClassTestTimer.stop(name=TimerNames.lastGenerationTime.value)
                            strFrmt = "%m-%Y%d days::%Hh:%Mm:%Ss"
                            message = ''.join(['Current generation step: ', str(count),
                                                '\nRemaining Steps: ', str(remainingSteps),
                                                '\nLast estimated time remaining: ', str(timerClassTestTimer.make_formatted_time(estimatedRemainingTime).split('::')[1]), ' seconds.',
                                                '\nLast generation time: ', str(timerClassTestTimer.make_formatted_time(lastGenerationTime).split('::')[1]), ' seconds.',
                                                '\nAverage generation time: ', str(timerClassTestTimer.make_formatted_time(averageGenerationTime).split('::')[1]), ' seconds.'])
                            for m in message.split('\n'):
                                logProg.warning(m)
                            
                            
                                
                    _progressDialog.progressValue += 1
                    
                    # lastGenerationTime = time.perf_counter() - generationStartTime
                    # averageGenerationTime = lastGenerationTime / count
                    
                    averageGenerationTime = ((count - 1) * averageGenerationTime + lastGenerationTime) / count
                    remainingSteps = _progressDialog.maximumValue - _progressDialog.progressValue
                    estimatedRemainingTime = remainingSteps * averageGenerationTime
                    
            
            # Make archive after bin-span for loop, archive everything in each modul folder
            _progressDialog.message = ProgressDialogString.getUpdatedMessage(
                currentVariation='',
                currentOperation=ProgressDialogString.OperationType.CREATING_ARCHIVE,
                operationTarget=new_folder_m
            )
            logProg.info("".join(["Creating archive '", new_folder_m, "'..."]))
            if os.path.exists("".join([new_folder_m, ".zip"])):
                logProg.info("...Archive already exists. Skipping...")
            else:
                shutil.make_archive(new_folder_m, "zip", new_folder_m)
                logProg.info("...DONE")
        
    else:

        for M in range(minimumModul, maximumModul + 1):
            # Begin the loop for Bin Span
            for bin_span in range(minimumBinSpan, maximumBinSpan + 1):
                # Begin the loop for part length
                for length in range(minimumLength, maximumLength + 1):
                    if _progressDialog.wasCancelled:
                        on_terminate(canceled=True)
                        return

                    if length % 2 == 0 or length % 5 == 0:
                        # Create the variant_name
                        variant_name = "".join(
                            [str(bin_span), "_span_M", str(M)]
                        )

                        logProg.info(
                            "".join(["Creating variant '", variant_name, "'..."])
                        )

                        # Construct the modul directory
                        new_folder_m = "".join([folder_root, "\\M", str(M)])
                        logProg.info("".join(["new_folder_m = ", new_folder_m]))
                        logProg.info(
                            "".join(["Making directory '", new_folder_m, "'"])
                        )
                        if overwriteExistingFiles or not os.path.isdir(
                            new_folder_m
                        ):
                            os.makedirs(new_folder_m, exist_ok=True)
                            logProg.info("...DONE")
                        else:
                            logProg.info("...Directory already exists.")

                        filename = "".join(
                            [new_folder_m, "\\", variant_name, ".stl"]
                        )

                        logProg.info("".join(["Filename='", filename, "'"]))
                        logProg.info("Checking if file already exists...")

                        if not overwriteExistingFiles and os.path.isfile(filename):
                            logProg.info("...File already exists. Skipping.")
                        else:
                            timerClassTestTimer.start(name=TimerNames.lastGenerationTime.value)
                            _progressDialog.message = ProgressDialogString.getUpdatedMessage(
                                currentVariation=variant_name,
                                currentOperation=ProgressDialogString.OperationType.CREATE_VARIANT,
                                operationTarget=filename,
                                elapsedTime=str((timerClassTestTimer.make_formatted_time(time.perf_counter() - generationStartTime)).split('::')[1]),
                                remainingTime=str((timerClassTestTimer.make_formatted_time(seconds=estimatedRemainingTime)).split('::')[1]),
                                averageTime=str((timerClassTestTimer.make_formatted_time(averageGenerationTime)).split('::')[1])
                            )

                            # Create the variant
                            logProg.warn(''.join(['Creating variant: ', variant_name]))
                            logProg.info(
                                "Setting Fusion 360 document parameters...."
                            )
                            param_bin_span.parameter.expression = str(bin_span)
                            param_m.parameter.expression = str(M)
                            param_label_text.parameter.comment = "".join(
                                ["M", str(M)]
                            )
                            logProg.info("...DONE")
                            logProg.debug(
                                "param_text_height.value prior to firing custom event: "
                                + str(param_text_height.value)
                            )

                            logProg.info("Firing custom events...")
                            _app.fireCustomEvent(
                                "thomasa88_ParametricText_Ext_Update"
                            )
                            adsk.doEvents()
                            adsk.doEvents()
                            logProg.info("...DONE")
                            logProg.debug(
                                "param_text_height after firing custom event: "
                                + str(param_text_height.value)
                            )
                            param_text_height.parameter.expression = "4mm"
                            logProg.debug(
                                "param_text_height after updating expression: "
                                + str(param_text_height.value)
                            )

                            # Save the file as an stl
                            logProg.info(
                                "".join(
                                    ["Exporting variant '", variant_name, "'..."]
                                )
                            )
                            exportMgr = adsk.fusion.ExportManager.cast(
                                _design.exportManager
                            )
                            stlOptions = exportMgr.createSTLExportOptions(
                                root_component
                            )
                            stlOptions.meshRefinement = adsk.fusion.MeshRefinementSettings.MeshRefinementMedium  # type: ignore
                            stlOptions.filename = filename
                            exportMgr.execute(stlOptions)
                            logProg.info("...DONE")

                            # Save a screenshot
                            if length == minimumLength or length == maximumLength:
                                logProg.info(
                                    "".join(
                                        [
                                            "Saving screenshot of variant '",
                                            variant_name,
                                            "'...",
                                        ]
                                    )
                                )
                                screenshot_filename = "".join(
                                    [
                                        folder_root,
                                        "\\_screenshots\\",
                                        variant_name,
                                        ".jpg",
                                    ]
                                )
                                _app.activeViewport.goHome(False)
                                _app.activeViewport.saveAsImageFile(
                                    screenshot_filename, 800, 500
                                )
                                logProg.info("...DONE")
                            count += 1
                            lastGenerationTime = timerClassTestTimer.stop(name=TimerNames.lastGenerationTime.value)
                            strFrmt = "%m-%Y%d days::%Hh:%Mm:%Ss"
                            message = ''.join(['Current generation step: ', str(count),
                                                '\nRemaining Steps: ', str(remainingSteps),
                                                '\nLast estimated time remaining: ', str(timerClassTestTimer.make_formatted_time(estimatedRemainingTime).split('::')[1]), ' seconds.',
                                                '\nLast generation time: ', str(timerClassTestTimer.make_formatted_time(lastGenerationTime).split('::')[1]), ' seconds.',
                                                '\nAverage generation time: ', str(timerClassTestTimer.make_formatted_time(averageGenerationTime).split('::')[1]), ' seconds.'])
                            for m in message.split('\n'):
                                logProg.warning(m)
                            
                            
                                
                    _progressDialog.progressValue += 1
                    
                    # lastGenerationTime = time.perf_counter() - generationStartTime
                    # averageGenerationTime = lastGenerationTime / count
                    
                    averageGenerationTime = ((count - 1) * averageGenerationTime + lastGenerationTime) / count
                    remainingSteps = _progressDialog.maximumValue - _progressDialog.progressValue
                    estimatedRemainingTime = remainingSteps * averageGenerationTime

    if not lengthDependentLabel:
        # Make archive after mopdul for loop, archive everything into one folder
        _progressDialog.message = ProgressDialogString.getUpdatedMessage(
            currentVariation='',
            currentOperation=ProgressDialogString.OperationType.CREATING_ARCHIVE,
            operationTarget=folder_root
        )
        logProg.info("".join(["Creating archive '", folder_root, "'..."]))
        shutil.make_archive(folder_root, "zip", folder_root)
        logProg.info("...DONE")

    logProg.info("JOB FINISHED. TERMINATING...")
    totalProcessTime = time.perf_counter() - generationStartTime
    message = ''.join(["Finished after ", str(timerClassTestTimer.make_formatted_time(totalProcessTime).split('::')[1]),
                        '\nLast estimated time remaining: ', str(timerClassTestTimer.make_formatted_time(estimatedRemainingTime).split('::')[1]),
                        '\nLast generation time: ', str(timerClassTestTimer.make_formatted_time(lastGenerationTime).split('::')[1]),
                        '\nAverage generation time: ', str(timerClassTestTimer.make_formatted_time(averageGenerationTime).split('::')[1])])
    for m in message.split('\n'):
        logProg.warning(m)
    on_terminate(canceled=False, message=message)


# Event handler for the execute event.
class MyCommandExecuteHandler(adsk.core.CommandEventHandler):
    def __init__(self):
        super().__init__()

    def notify(self, args):
        try:
            executeScrewBoltNutWasher(args)

        except:
            on_exception()
            return


# Event handler that reacts to any changes the user makes to any of the command inputs.
class MyCommandInputChangedHandler(adsk.core.InputChangedEventHandler):
    def __init__(self):
        super().__init__()

    def notify(self, args):
        try:
            eventArgs = adsk.core.InputChangedEventArgs.cast(args)
            inputs = eventArgs.inputs
            cmdInput = eventArgs.input

            if cmdInput.id == CommandInputId.LENGTH_DEPENDENT_LABEL:
                if _screwBoltNutWasher_lengthDependentLabel.value:
                    _screwBoltNutWasher_minimumLength.isVisible = True
                    _screwBoltNutWasher_maximumLength.isVisible = True
                else:
                    _screwBoltNutWasher_minimumLength.isVisible = False
                    _screwBoltNutWasher_maximumLength.isVisible = False

        except:
            on_exception()
            return


# Event handler for the validateInputs event.
class MyCommandValidateInputsHandler(adsk.core.ValidateInputsEventHandler):
    def __init__(self):
        super().__init__()

    def notify(self, args):
        try:
            eventArgs = adsk.core.ValidateInputsEventArgs.cast(args)

            _errMessage.text = ""

            if _screwBoltNutWasher_minimumLength.value >= _screwBoltNutWasher_maximumLength.value:
                _errMessage.text = (
                    CommandInputId.MINIMUM_LENGTH
                    + " must be less than "
                    + CommandInputId.MAXIMUM_LENGTH
                )
                eventArgs.areInputsValid = False
                return
            if _screwBoltNutWasher_minimumModul.value >= _screwBoltNutWasher_maximumModul.value:
                _errMessage.text = (
                    CommandInputId.MINIMUM_MODUL
                    + " must be less than "
                    + CommandInputId.MAXIMUM_MODUL
                )
                eventArgs.areInputsValid = False
                return
            if _screwBoltNutWasher_minimumBinSpan.value >= _screwBoltNutWasher_maximumBinSpan.value:
                _errMessage.text = (
                    CommandInputId.MINIMUM_BIN_SPAN
                    + " must be less than "
                    + CommandInputId.MAXIMUM_BIN_SPAN
                )
                eventArgs.areInputsValid = False
                return

        except:
            on_exception()
            return
