"""A centralized module to simplify imports.
All tat is needed is to include `from .imports import *`
With each directory level down from root just add another `.`
e.g.
    For a file in 'root/commands', use `from ..imports import *`

    For a file in 'root/commands/commandDialog' use `from ...imports import *`

Some imports that are often used in conjunction have been grouped into separate sub-modules, such as 'imports.jsonSchema'.
If quick access to the imports within this sub-module is required, simply use:

```
from .imports import *
from jsonSchema import *
```
"""

from .src import commands
from .lib import fusionAddInUtils as futil
from . import R


def __init__():
    pass
