from enum import StrEnum

class ProgressDialogString:
    """
    File and variant operation types and their respective message
    """
    
    @staticmethod
    def getUpdatedMessage(
        currentVariation="",
        currentOperation="",
        operationTarget="",
        elapsedTime="",
        remainingTime="",
        averageTime="",
    ):
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
            avgTime=averageTime,
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
