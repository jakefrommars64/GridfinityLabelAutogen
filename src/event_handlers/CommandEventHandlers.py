import adsk
from enum import Enum, IntEnum, StrEnum
import logging
import traceback

from screw_generation import executeScrewBoltNutWasher


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


class ProgressExceptionUIMixin(object):
    def on_exception(self, app):
        logProg = logging.getLogger("ProgressLogger")
        e = "Failed:\n{}".format(traceback.format_exc())
        logProg.critical(e)
        
        app.userInterface.messageBox(e)


class CommandDestroyHandler(adsk.core.CommandEventHandler, ProgressExceptionUIMixin):
    """
    Event handler that reacts to when the command is destroyed. This terminates the script.
    """
    
    def __init__(self):
        super().__init__()

    def notify(self, args):
        _app = adsk.core.Application.get()
        
        try:
            # When the command is done, terminate the script
            # on_terminate()
            # This will release all globals which will remove all event handlers
            _app.log("Command Destroy handler called")
            adsk.terminate()
        except:
            self.on_exception(_app)
            
            return


class CommandExecuteHandler(adsk.core.CommandEventHandler, ProgressExceptionUIMixin):
    """
    Acts upon instances of a CommandEvent
    """
    def __init__(self, on_terminated_handler: function):
        super().__init__()
        self.on_terminate = on_terminated_handler

    def notify(self, args):
        try:
            executeScrewBoltNutWasher(self.on_terminate, args)

        except:
            _app = adsk.core.Application.get()
            self.on_exception(_app)
            
            return



class CommandInputChangedHandler(adsk.core.InputChangedEventHandler):
    """
    Event handler that reacts to any changes the user makes to any of the command inputs.
    """
    
    def __init__(self):
        super().__init__()

    def notify(self, args):
        _app = adsk.core.Application.get()
        
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
            self.on_exception(_app)
            return


# Event handler for the validateInputs event.
class CommandValidateInputsHandler(adsk.core.ValidateInputsEventHandler, ProgressExceptionUIMixin):
    def __init__(self):
        super().__init__()

    def notify(self, args):
        _app = adsk.core.Application.get()
        
        try:
            eventArgs = adsk.core.ValidateInputsEventArgs.cast(args)

            _errMessage.text = ""

            if (
                _screwBoltNutWasher_minimumLength.value
                >= _screwBoltNutWasher_maximumLength.value
            ):
                _errMessage.text = (
                    CommandInputId.MINIMUM_LENGTH
                    + " must be less than "
                    + CommandInputId.MAXIMUM_LENGTH
                )
                eventArgs.areInputsValid = False
                return
            if (
                _screwBoltNutWasher_minimumModul.value
                >= _screwBoltNutWasher_maximumModul.value
            ):
                _errMessage.text = (
                    CommandInputId.MINIMUM_MODUL
                    + " must be less than "
                    + CommandInputId.MAXIMUM_MODUL
                )
                eventArgs.areInputsValid = False
                return
            if (
                _screwBoltNutWasher_minimumBinSpan.value
                >= _screwBoltNutWasher_maximumBinSpan.value
            ):
                _errMessage.text = (
                    CommandInputId.MINIMUM_BIN_SPAN
                    + " must be less than "
                    + CommandInputId.MAXIMUM_BIN_SPAN
                )
                eventArgs.areInputsValid = False
                return

        except:
            self.on_exception(_app)
            return


class CommandCreatedHandler(adsk.core.CommandCreatedEventHandler, ProgressExceptionUIMixin):
    """
    Event handler that reacts when the command definition is executed which
    results in the command being created and this event being fired.
    """
    
    def __init__(self, on_terminated_handler):
        super().__init__()
        self.on_terminated = on_terminated_handler

    def notify(self, args):
        
        _app = adsk.core.Application.get()
        
        try:
            global _progressDialog, _design, _cmdDef
            global _progressDialog, _rootFolderName, _screwBoltNutWasher_lengthDependentLabel, _screwBoltNutWasher_minimumLength, _screwBoltNutWasher_maximumLength
            global _screwBoltNutWasher_minimumModul, _screwBoltNutWasher_maximumModul, _screwBoltNutWasher_minimumBinSpan, _screwBoltNutWasher_maximumBinSpan, _overwriteExistingFiles, _errMessage
            global _handlers, _generationAlgorithm
            eventArgs = adsk.core.CommandCreatedEventArgs.cast(args)

            if not _design:
                _app.userInterface.messageBox(
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
                adsk.core.DropDownStyles.TextListDropDownStyle,  # type: ignore
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
            onExecute = CommandExecuteHandler(self.on_terminated)
            _cmd.execute.add(onExecute)
            _handlers.append(onExecute)

            onInputChanged = CommandInputChangedHandler()
            _cmd.inputChanged.add(onInputChanged)
            _handlers.append(onInputChanged)

            onValidateInputs = CommandValidateInputsHandler()
            _cmd.validateInputs.add(onValidateInputs)
            _handlers.append(onValidateInputs)

            onDestroy = CommandDestroyHandler()
            _cmd.destroy.add(onDestroy)
            _handlers.append(onDestroy)

        except:
            self.on_exception(_app)
            return
