"""Importing this module will allow access to all `res/` files.
"""

import pathlib

# LABEL_DOCUMENT_PARAMETERS_SCHEMA = "res/schema/label_document_parameters_schema.json"

LABEL_DOCUMENT_PARAMETERS_SCHEMA = pathlib.Path(__file__).parent.parent.joinpath(
    "res\schema\label_document_parameters_schema.json"
)
