import stat
import shutil
import logging
from shutil import copytree
import sys
import os
import pathlib

homeDir = pathlib.Path(os.environ["HOME"])
devPath = pathlib.Path(sys.argv[1])
deployDir = homeDir.joinpath(
    "AppData\Roaming\Autodesk\ApplicationPlugins").joinpath(f"{sys.argv[2]}.bundle")

print("Building add-in...")
print(f"HOME = {homeDir}")
print(f"DEVELOPMENT PATH = {devPath}")
print(f"DEPLOY DIR = {deployDir}")


def _logpath(path, names):
    logging.info('Working in %s', path)
    # nothing will be ignored
    return [".git", ".github", ".vscode", ".gitignore", "build.py"]


def remove_readonly(func, path, _):
    "Clear the readonly bit and reattempt the removal"
    os.chmod(path, stat.S_IWRITE)
    func(path)


shutil.rmtree(deployDir, onerror=remove_readonly)


copytree(devPath, deployDir, ignore=_logpath)
