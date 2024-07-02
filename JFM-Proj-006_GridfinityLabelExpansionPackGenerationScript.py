# Author-jakefrommars64
# Description-

import adsk.core, adsk.fusion, adsk.cam, traceback
import os
import shutil
import math


def run(context):
    def _CANCEL_IMPL():
        ui.messageBox("Canceled by user")
        return

    ui = None
    try:
        app = adsk.core.Application.get()
        ui = app.userInterface
        design = adsk.fusion.Design.cast(app.activeProduct)

        ui.messageBox("Hello World!")
    except:
        if ui:
            ui.messageBox("Failed:\n{}".format(traceback.format_exc()))
