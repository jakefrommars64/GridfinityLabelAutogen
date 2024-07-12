import pytest
from ..imports_and_dependencies import *


def test_readJsonSchema():
    import pathlib
    from jschon import create_catalog, JSON, JSONSchema

    schema_dir = pathlib.Path(__file__).parent / "res/schemas"
    print(schema_dir)
