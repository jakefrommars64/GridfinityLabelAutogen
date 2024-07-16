import pathlib
import adsk.fusion, adsk.core
from ..lib import fusionAddInUtils as futil
import json
from .. import R


class JSONSchema:

    def __init__(self, fp: pathlib.Path):
        """_summary_

        Args:
            fp (pathlib.Path): a pathlib.Path object pointing to a JSON schema document.
        """
        self.path = fp
        self.schema = None
        self.id = None
        self.title = None
        self.description = None
        self.properties = {}
        self.required = []

    def load(self):
        json_obj = json.load(self.path.open())
        self.schema = json_obj["$schema"]
        self.id = json_obj["$id"]
        self.title = json_obj["title"]
        self.description = json_obj["description"]
        self.required = json_obj["required"]

        futil.log(f"$schema: {self.schema}")
        futil.log(f"$id: {self.id}")
        futil.log(f"title: {self.title}")
        futil.log(f"description: {self.description}")
        futil.log(f"required: {self.required}")

        for p in json_obj["properties"]:
            self.properties[p] = {}
            for key in json_obj["properties"][p]:
                self.properties[p][key] = json_obj["properties"][p][key]
            futil.log(f"{p}: {self.properties[p]}")

    def validate(self, props: dict):
        futil.log(f"Validating...")
        val_props = {}
        for p in props:
            if not p in self.properties:
                continue
            val_props[p] = props[p]
        return val_props


class DesignParameters:
    def __init__(self, _design: adsk.fusion.Design):
        self.design = _design
        self.parameters = {}
        self.read_design_parameters()

    def read_design_parameters(self):
        for i in range(self.design.allParameters.count):
            param = self.design.allParameters.item(i)
            self.parameters[param.name] = {
                "comment": param.comment,
                "unit": param.unit,
                "expression": param.expression,
                "value": param.value,
            }
            futil.log(f"{param.name}: {self.parameters[param.name]}")
