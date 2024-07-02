# This script is what will be called by Fusion 360.
# This will be the entry point into the rest of the add-in.

import adsk.core, adsk.fusion, traceback


def run(context):
    ui = None
    try:
        app = adsk.core.Application.get()
        ui = app.userInterface
        ui.messageBox("Hello addin")
    except:
        if ui:
            ui.messageBox("Failed:\n{}".format(traceback.format_exc()))


def stop(context):
    ui = None
    try:
        app = adsk.core.Application.get()
        ui = app.userInterface
        ui.messageBox("Stop addin")
    except:
        if ui:
            ui.messageBox("Failed:\n{}".format(traceback.format_exc()))
