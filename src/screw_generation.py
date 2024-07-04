
import os, shutil
import time
from enum import StrEnum
import logging

import adsk

from messaging import ProgressDialogString
from src.timing import Timer, TimerNames
import settings


class DesignAttributeId(StrEnum):
    """
    ID strings for design attributes
    """
    # Group Names
    GROUP_SCRIPT_NAME = settings.LABEL_SCRIPT_NAME

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


class DesignParameter:
    """
    Design parameters definition class that holds parameters from the design and make them
    easier to work with down the road
    """
    
    def __init__(self, name: str, design: adsk.fusion.Design):
        self.name = name
        self.parameter = design.allParameters.itemByName(self.name)
        if not self.parameter:
            self.exists = False
        else:
            self.value = self.parameter.value
            self.exists = True
            
    
def executeScrewBoltNutWasher(on_terminate: function, timer:Timer, args):
    global _progressDialog, _design, _cmdDef
    global _progressDialog, _rootFolderName, _screwBoltNutWasher_lengthDependentLabel, _screwBoltNutWasher_minimumLength, _screwBoltNutWasher_maximumLength
    global _screwBoltNutWasher_minimumModul, _screwBoltNutWasher_maximumModul, _screwBoltNutWasher_minimumBinSpan, _screwBoltNutWasher_maximumBinSpan
    global _overwriteExistingFiles, _errMessage
    global _handlers, processTimerStart
    eventArgs = adsk.core.CommandEventArgs.cast(args)
    _app = adsk.core.Application.get()

    # Save the current values as attributes
    attribs = _design.attributes
    logProg = logging.getLogger("ProgressLogger")
    
    logProg.warn("Saving current command parameters to design attributes...")
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
        DesignAttributeId.GROUP_SCRIPT_NAME, DesignAttributeId.ROOT_FOLDER_NAME
    ).value
    lengthDependentLabel = (
        True
        if attribs.itemByName(
            DesignAttributeId.GROUP_SCRIPT_NAME,
            DesignAttributeId.SBNW_LENGTH_DEPENDENT_LABEL,
        ).value
        == "True"
        else False
    )
    minimumLength = int(
        attribs.itemByName(
            DesignAttributeId.GROUP_SCRIPT_NAME, DesignAttributeId.SBNW_MINIMUM_LENGTH
        ).value
    )
    maximumLength = int(
        attribs.itemByName(
            DesignAttributeId.GROUP_SCRIPT_NAME, DesignAttributeId.SBNW_MAXIMUM_LENGTH
        ).value
    )
    minimumModul = int(
        attribs.itemByName(
            DesignAttributeId.GROUP_SCRIPT_NAME, DesignAttributeId.SBNW_MINIMUM_MODUL
        ).value
    )
    maximumModul = int(
        attribs.itemByName(
            DesignAttributeId.GROUP_SCRIPT_NAME, DesignAttributeId.SBNW_MAXIMUM_MODUL
        ).value
    )
    minimumBinSpan = int(
        attribs.itemByName(
            DesignAttributeId.GROUP_SCRIPT_NAME, DesignAttributeId.SBNW_MINIMUM_BIN_SPAN
        ).value
    )
    maximumBinSpan = int(
        attribs.itemByName(
            DesignAttributeId.GROUP_SCRIPT_NAME, DesignAttributeId.SBNW_MAXIMUM_BIN_SPAN
        ).value
    )
    overwriteExistingFiles = (
        True
        if attribs.itemByName(
            DesignAttributeId.GROUP_SCRIPT_NAME,
            DesignAttributeId.OVERWRITE_EXISTING_FILES,
        ).value
        == "True"
        else False
    )

    logProg.warn("Get operation parameter values...")
    logProg.warn("".join(["rootFolderName = ", str(rootFolderName)]))
    logProg.warn("".join(["lengthDependentLabel = ", str(lengthDependentLabel)]))
    logProg.warn("".join(["minimumLength = ", str(minimumLength)]))
    logProg.warn("".join(["maximumLength = ", str(maximumLength)]))
    logProg.warn("".join(["minimumModul = ", str(minimumModul)]))
    logProg.warn("".join(["maximumModul = ", str(maximumModul)]))
    logProg.warn("".join(["minimumBinSpan = ", str(minimumBinSpan)]))
    logProg.warn("".join(["maximumBinSpan = ", str(maximumBinSpan)]))
    logProg.warn("".join(["overwriteExistingFiles = ", str(overwriteExistingFiles)]))

    # Create temp and debug folders if necessary
    if not os.path.isdir(settings.TEMP_DIR):
        os.makedirs(settings.TEMP_DIR)
    if not os.path.isdir(settings.DEBUG_DIR):
        os.makedirs(settings.DEBUG_DIR)

    if settings.DEBUG_MODE:
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
    timer.start(name=TimerNames.AutogenerationLoopTimer.value)

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
    _progressDialog = _app.userInterface.createProgressDialog()
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
                        logProg.info("".join(["Making directory '", new_folder_m, "'"]))
                        if overwriteExistingFiles or not os.path.isdir(new_folder_m):
                            os.makedirs(new_folder_m, exist_ok=True)
                            logProg.info("...DONE")
                        else:
                            logProg.info("...Directory already exists.")

                        # If lengthDependentLabel then construct the span directory
                        new_folder_span = "".join(
                            [new_folder_m, "\\", str(bin_span), "_span"]
                        )
                        logProg.info("".join(["new_folder_span = ", new_folder_span]))
                        logProg.info(
                            "".join(["Making directory '", new_folder_span, "'"])
                        )
                        if overwriteExistingFiles or not os.path.isdir(new_folder_span):
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
                            timer.start(
                                name=TimerNames.lastGenerationTime.value
                            )
                            _progressDialog.message = ProgressDialogString.getUpdatedMessage(
                                currentVariation=variant_name,
                                currentOperation=ProgressDialogString.OperationType.CREATE_VARIANT,
                                operationTarget=filename,
                                elapsedTime=str(
                                    (
                                        timer.make_formatted_time(
                                            time.perf_counter() - generationStartTime
                                        )
                                    ).split("::")[1]
                                ),
                                remainingTime=str(
                                    (
                                        timer.make_formatted_time(
                                            seconds=estimatedRemainingTime
                                        )
                                    ).split("::")[1]
                                ),
                                averageTime=str(
                                    (
                                        timer.make_formatted_time(
                                            averageGenerationTime
                                        )
                                    ).split("::")[1]
                                ),
                            )

                            # Create the variant
                            logProg.warn("".join(["Creating variant: ", variant_name]))
                            logProg.info("Setting Fusion 360 document parameters....")
                            
                            param_bin_span.parameter.expression = str(bin_span)
                            param_m.parameter.expression = str(M)
                            param_label_text.parameter.comment = "".join(["M", str(M)])
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
                            _app.fireCustomEvent("thomasa88_ParametricText_Ext_Update")
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
                                "".join(["Exporting variant '", variant_name, "'..."])
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
                            lastGenerationTime = timer.stop(
                                name=TimerNames.lastGenerationTime.value
                            )
                            strFrmt = "%m-%Y%d days::%Hh:%Mm:%Ss"
                            message = "".join(
                                [
                                    "Current generation step: ",
                                    str(count),
                                    "\nRemaining Steps: ",
                                    str(remainingSteps),
                                    "\nLast estimated time remaining: ",
                                    str(
                                        timer.make_formatted_time(
                                            estimatedRemainingTime
                                        ).split("::")[1]
                                    ),
                                    " seconds.",
                                    "\nLast generation time: ",
                                    str(
                                        timer.make_formatted_time(
                                            lastGenerationTime
                                        ).split("::")[1]
                                    ),
                                    " seconds.",
                                    "\nAverage generation time: ",
                                    str(
                                        timer.make_formatted_time(
                                            averageGenerationTime
                                        ).split("::")[1]
                                    ),
                                    " seconds.",
                                ]
                            )
                            for m in message.split("\n"):
                                logProg.warning(m)

                    _progressDialog.progressValue += 1

                    # lastGenerationTime = time.perf_counter() - generationStartTime
                    # averageGenerationTime = lastGenerationTime / count

                    averageGenerationTime = (
                        (count - 1) * averageGenerationTime + lastGenerationTime
                    ) / count
                    remainingSteps = (
                        _progressDialog.maximumValue - _progressDialog.progressValue
                    )
                    estimatedRemainingTime = remainingSteps * averageGenerationTime

            # Make archive after bin-span for loop, archive everything in each modul folder
            _progressDialog.message = ProgressDialogString.getUpdatedMessage(
                currentVariation="",
                currentOperation=ProgressDialogString.OperationType.CREATING_ARCHIVE,
                operationTarget=new_folder_m,
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
                        variant_name = "".join([str(bin_span), "_span_M", str(M)])

                        logProg.info(
                            "".join(["Creating variant '", variant_name, "'..."])
                        )

                        # Construct the modul directory
                        new_folder_m = "".join([folder_root, "\\M", str(M)])
                        logProg.info("".join(["new_folder_m = ", new_folder_m]))
                        logProg.info("".join(["Making directory '", new_folder_m, "'"]))
                        if overwriteExistingFiles or not os.path.isdir(new_folder_m):
                            os.makedirs(new_folder_m, exist_ok=True)
                            logProg.info("...DONE")
                        else:
                            logProg.info("...Directory already exists.")

                        filename = "".join([new_folder_m, "\\", variant_name, ".stl"])

                        logProg.info("".join(["Filename='", filename, "'"]))
                        logProg.info("Checking if file already exists...")

                        if not overwriteExistingFiles and os.path.isfile(filename):
                            logProg.info("...File already exists. Skipping.")
                        else:
                            timer.start(
                                name=TimerNames.lastGenerationTime.value
                            )
                            _progressDialog.message = ProgressDialogString.getUpdatedMessage(
                                currentVariation=variant_name,
                                currentOperation=ProgressDialogString.OperationType.CREATE_VARIANT,
                                operationTarget=filename,
                                elapsedTime=str(
                                    (
                                        timer.make_formatted_time(
                                            time.perf_counter() - generationStartTime
                                        )
                                    ).split("::")[1]
                                ),
                                remainingTime=str(
                                    (
                                        timer.make_formatted_time(
                                            seconds=estimatedRemainingTime
                                        )
                                    ).split("::")[1]
                                ),
                                averageTime=str(
                                    (
                                        timer.make_formatted_time(
                                            averageGenerationTime
                                        )
                                    ).split("::")[1]
                                ),
                            )

                            # Create the variant
                            logProg.warn("".join(["Creating variant: ", variant_name]))
                            logProg.info("Setting Fusion 360 document parameters....")
                            param_bin_span.parameter.expression = str(bin_span)
                            param_m.parameter.expression = str(M)
                            param_label_text.parameter.comment = "".join(["M", str(M)])
                            logProg.info("...DONE")
                            logProg.debug(
                                "param_text_height.value prior to firing custom event: "
                                + str(param_text_height.value)
                            )

                            logProg.info("Firing custom events...")
                            _app.fireCustomEvent("thomasa88_ParametricText_Ext_Update")
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
                                "".join(["Exporting variant '", variant_name, "'..."])
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
                            lastGenerationTime = timer.stop(
                                name=TimerNames.lastGenerationTime.value
                            )
                            strFrmt = "%m-%Y%d days::%Hh:%Mm:%Ss"
                            message = "".join(
                                [
                                    "Current generation step: ",
                                    str(count),
                                    "\nRemaining Steps: ",
                                    str(remainingSteps),
                                    "\nLast estimated time remaining: ",
                                    str(
                                        timer.make_formatted_time(
                                            estimatedRemainingTime
                                        ).split("::")[1]
                                    ),
                                    " seconds.",
                                    "\nLast generation time: ",
                                    str(
                                        timer.make_formatted_time(
                                            lastGenerationTime
                                        ).split("::")[1]
                                    ),
                                    " seconds.",
                                    "\nAverage generation time: ",
                                    str(
                                        timer.make_formatted_time(
                                            averageGenerationTime
                                        ).split("::")[1]
                                    ),
                                    " seconds.",
                                ]
                            )
                            for m in message.split("\n"):
                                logProg.warning(m)

                    _progressDialog.progressValue += 1

                    # lastGenerationTime = time.perf_counter() - generationStartTime
                    # averageGenerationTime = lastGenerationTime / count

                    averageGenerationTime = (
                        (count - 1) * averageGenerationTime + lastGenerationTime
                    ) / count
                    remainingSteps = (
                        _progressDialog.maximumValue - _progressDialog.progressValue
                    )
                    estimatedRemainingTime = remainingSteps * averageGenerationTime

    if not lengthDependentLabel:
        # Make archive after mopdul for loop, archive everything into one folder
        _progressDialog.message = ProgressDialogString.getUpdatedMessage(
            currentVariation="",
            currentOperation=ProgressDialogString.OperationType.CREATING_ARCHIVE,
            operationTarget=folder_root,
        )
        logProg.info("".join(["Creating archive '", folder_root, "'..."]))
        shutil.make_archive(folder_root, "zip", folder_root)
        logProg.info("...DONE")

    logProg.info("JOB FINISHED. TERMINATING...")
    totalProcessTime = time.perf_counter() - generationStartTime
    message = "".join(
        [
            "Finished after ",
            str(
                timer.make_formatted_time(totalProcessTime).split("::")[1]
            ),
            "\nLast estimated time remaining: ",
            str(
                timer.make_formatted_time(estimatedRemainingTime).split(
                    "::"
                )[1]
            ),
            "\nLast generation time: ",
            str(
                timer.make_formatted_time(lastGenerationTime).split("::")[
                    1
                ]
            ),
            "\nAverage generation time: ",
            str(
                timer.make_formatted_time(averageGenerationTime).split(
                    "::"
                )[1]
            ),
        ]
    )
    for m in message.split("\n"):
        logProg.warning(m)
    on_terminate(canceled=False, message=message)

