from ...lib import design_parameters
import adsk.core
import adsk.fusion
import os
from ...lib import fusionAddInUtils as futil
from ... import config
from ...lib import R

app = adsk.core.Application.get()
ui = app.userInterface


# TODO *** Specify the command identity information. ***
CMD_ID = f"{config.COMPANY_NAME}_{config.ADDIN_NAME}_generateLabel"
CMD_NAME = "Generate Label"
CMD_Description = "Generate a label using parameters input by the user."
futil.log(CMD_ID)

# Specify that the command will be promoted to the panel.
IS_PROMOTED = True

# TODO *** Define the location where the command button will be created. ***
# This is done by specifying the workspace, the tab, and the panel, and the
# command it will be inserted beside. Not providing the command to position it
# will insert it at the end.
WORKSPACE_ID = "FusionSolidEnvironment"
TAB_ID = "SolidTab"
PANEL_BESIDE_ID = "SolidModifyPanel"
PANEL_ID = "AutogeneratePanel"
COMMAND_BESIDE_ID = ""

# Resource location for command icons, here we assume a sub folder in this directory named "resources".
ICON_FOLDER = os.path.join(os.path.dirname(
    os.path.abspath(__file__)), "resources", "")

# Local list of event handlers used to maintain a reference so
# they are not released and garbage collected.
local_handlers = []


# Executed when add-in is run.
def start():
    # Create a command Definition.
    if not ui.commandDefinitions.itemById(CMD_ID):
        cmd_def = ui.commandDefinitions.addButtonDefinition(
            CMD_ID, CMD_NAME, CMD_Description, ICON_FOLDER
        )
    cmd_def = ui.commandDefinitions.itemById(CMD_ID)

    # Define an event handler for the command created event. It will be called when the button is clicked.
    futil.add_handler(cmd_def.commandCreated, command_created)

    # ******** Add a button into the UI so the user can run the command. ********
    # Get the target workspace the button will be created in.
    workspace = ui.workspaces.itemById(WORKSPACE_ID)

    # Get the tab the button will be created in.
    tab = workspace.toolbarTabs.itemById(TAB_ID)

    # Get the panel the button will be created in.
    panel = tab.toolbarPanels.itemById(PANEL_ID)
    if not panel:
        panel = tab.toolbarPanels.add(
            PANEL_ID, "Autogenerate", PANEL_BESIDE_ID, False)

    # Create the button command control in the UI after the specified existing command.
    control = panel.controls.addCommand(cmd_def, COMMAND_BESIDE_ID, False)

    # Specify if the command is promoted to the main toolbar.
    control.isPromoted = IS_PROMOTED


# Executed when add-in is stopped.
def stop():
    # Get the various UI elements for this command
    workspace = ui.workspaces.itemById(WORKSPACE_ID)
    panel = workspace.toolbarPanels.itemById(PANEL_ID)
    command_control = panel.controls.itemById(CMD_ID)
    command_definition = ui.commandDefinitions.itemById(CMD_ID)

    # Delete the button command control
    if command_control:
        command_control.deleteMe()

    # Delete the command definition
    if command_definition:
        command_definition.deleteMe()


def get_and_validate_design_parameters():
    """Get Fusion 360 design parameters,
    check if it has a parameter named `gla-id`,
    validate design parameters against schema.
    """

    futil.log(f"Getting document design parameters...")
    _app = adsk.core.Application.get()
    _design = adsk.fusion.Design.cast(_app.activeProduct)

    design_params = design_parameters.DesignParameters(_design)

    # check if design has parameter named `gla_id`
    # if not then display message to open a GLA document.
    # Otherwise Continue and valiudate design parameters.
    if not design_params.parameters.get("gla_id"):
        futil.log("Currently open document is not a GLA document.")
        ui.messageBox("Please open an official GLA Fusion 360 Document.")
        return 0

    futil.log(f"Loading label design parameters schema...")
    dp_schema = design_parameters.JSONSchema(
        R.LABEL_DOCUMENT_PARAMETERS_SCHEMA)
    dp_schema.load()
    val_props = dp_schema.validate(design_params.parameters)
    return design_params


# Function that is called when a user clicks the corresponding button in the UI.
# This defines the contents of the command dialog and connects to the command related events.
def command_created(args: adsk.core.CommandCreatedEventArgs):
    # General logging for debug.
    futil.log(f"{CMD_NAME} Command Created Event")

    global design_params
    design_params = get_and_validate_design_parameters()
    if design_params == 0:
        return

    # https://help.autodesk.com/view/fusion360/ENU/?contextId=CommandInputs
    inputs = args.command.commandInputs

    # TODO Define the dialog for your command by adding different inputs to the command.
    # TODO Define JSON schema and schema loader for commandInputs

    # Create a simple text box input.
    inputs.addTextBoxCommandInput(
        "text_box", "Some Text", "Enter some text.", 1, False)
    inputs.addIntegerSpinnerCommandInput(
        id="bin_span_spinner", name="Bin Span", initialValue=1, min=1, max=100, spinStep=1)

    # TODO Connect to the events that are needed by this command.
    futil.add_handler(
        args.command.execute, command_execute, local_handlers=local_handlers
    )
    futil.add_handler(
        args.command.inputChanged, command_input_changed, local_handlers=local_handlers
    )
    futil.add_handler(
        args.command.executePreview, command_preview, local_handlers=local_handlers
    )
    futil.add_handler(
        args.command.validateInputs,
        command_validate_input,
        local_handlers=local_handlers,
    )
    futil.add_handler(
        args.command.destroy, command_destroy, local_handlers=local_handlers
    )


# This event handler is called when the user clicks the OK button in the command dialog or
# is immediately called after the created event not command inputs were created for the dialog.
def command_execute(args: adsk.core.CommandEventArgs):
    # General logging for debug.
    futil.log(f"{CMD_NAME} Command Execute Event")

    # TODO ******************************** Your code here ********************************

    # Get a reference to your command's inputs.
    inputs = args.command.commandInputs
    text_box: adsk.core.TextBoxCommandInput = inputs.itemById("text_box")
    bin_span_spinner: adsk.core.IntegerSpinnerCommandInput = inputs.itemById(
        "bin_span_spinner")

    # Update and save the variable bin_span to the new value.
    text = text_box.text
    new_bin_span_expression = bin_span_spinner.value
    design_params.preview_parameter_expression(
        "bin_span", str(new_bin_span_expression))
    futil.log(
        f'Execute changed Design Parameter \'bin_span\' to {new_bin_span_expression}')


# This event handler is called when the command needs to compute a new preview in the graphics window.
def command_preview(args: adsk.core.CommandEventArgs):
    # General logging for debug.
    futil.log(f"{CMD_NAME} Command Preview Event")
    inputs = args.command.commandInputs
    bin_span_spinner: adsk.core.IntegerSpinnerCommandInput = inputs.itemById(
        "bin_span_spinner")

    # Update the preview to show the label with the new bin_span value.
    new_bin_span_expression = bin_span_spinner.value
    design_params.preview_parameter_expression(
        "bin_span", str(new_bin_span_expression))
    futil.log(
        f'Preview changed Design Parameter \'bin_span\' to {new_bin_span_expression}')


# This event handler is called when the user changes anything in the command dialog
# allowing you to modify values of other inputs based on that change.
def command_input_changed(args: adsk.core.InputChangedEventArgs):
    changed_input = args.input
    inputs = args.inputs

    # General logging for debug.
    futil.log(
        f"{CMD_NAME} Input Changed Event fired from a change to {changed_input.id}"
    )


# This event handler is called when the user interacts with any of the inputs in the dialog
# which allows you to verify that all of the inputs are valid and enables the OK button.
def command_validate_input(args: adsk.core.ValidateInputsEventArgs):
    # General logging for debug.
    futil.log(f"{CMD_NAME} Validate Input Event")

    inputs = args.inputs

    # Verify the validity of the input values. This controls if the OK button is enabled or not.
    binSpanSpinner = inputs.itemById("bin_span_spinner")
    if binSpanSpinner.value >= 1:
        args.areInputsValid = True
    else:
        args.areInputsValid = False


# This event handler is called when the command terminates.
def command_destroy(args: adsk.core.CommandEventArgs):
    # General logging for debug.
    futil.log(f"{CMD_NAME} Command Destroy Event")

    global local_handlers
    local_handlers = []
