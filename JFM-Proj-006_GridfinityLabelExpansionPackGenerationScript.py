# Author-jakefrommars64
# Description-

# the name of the Python file and, incidentally, the name of the script in Fusion 360
_script_name_ = "gridfinity_label_autogen"

from datetime import datetime
from enum import Enum
import time
from adsk.core import Application
import adsk.core
import adsk.fusion
import traceback

import logging

from src import settings
from src.timing import Timer, TimerNames
from src.event_handlers.CommandEventHandlers import CommandCreatedHandler, CommandInputId
from src.screw_generation import DesignAttributeId


# Set up the loggers

_log_formatter = logging.Formatter(fmt=settings.LOG_FORMAT)
logfile_handler = logging.FileHandler(
    filename="".join(
        [settings.LOG_DIR, "debug_", datetime.now().strftime("%d-%m-%Y-%H-%M-%S"), ".log"]
    ),
    mode="w",
)
logfile_handler.setLevel(logging.DEBUG)
logfile_handler.setFormatter(fmt=_log_formatter)

logProg = logging.getLogger("ProgressLogger")
logProg.setLevel(logging.DEBUG)
logProg.addHandler(logfile_handler)
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

# Global autogen parameters
_screwBoltNutWasher_minimumBinSpan = adsk.core.IntegerSpinnerCommandInput.cast(None)
_screwBoltNutWasher_maximumBinSpan = adsk.core.IntegerSpinnerCommandInput.cast(None)
_overwriteExistingFiles = adsk.core.BoolValueCommandInput.cast(None)
_errMessage = adsk.core.TextBoxCommandInput.cast(None)

processTimerStart = time.perf_counter()
timerClassTestTimer = Timer(
    logger=Application.log, time_frmt="%m-%Y::%d days:%Hh:%Mm:%Ss"
)


# Global set of event handlers to keep them referenced for the duration of the command
_handlers = []

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
            settings.DEBUG_DIR,
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
        # TODO: fix function handling
        onCommandCreated = CommandCreatedHandler(on_terminated_handler=on_terminate)
        _cmdDef.commandCreated.add(onCommandCreated)
        _handlers.append(onCommandCreated)

        # Execute the command definition.
        _cmdDef.execute()

        # Prevent this module from being terminated when the script returns, because we are waiting for event handlers to fire.
        adsk.autoTerminate(False)

    except:
        on_exception()
        return

