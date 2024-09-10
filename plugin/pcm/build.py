import os
import shutil
from pathlib import Path
import json
import re

plugin_src_path = (Path(__file__).parent.parent / "src").absolute()
resources_path = Path(__file__).parent / "resources"
repo_path = (Path(__file__).parent.parent.parent).absolute()
board2pdf_src_path = repo_path / "src" / "board2pdf"

build_path = Path("build").absolute()

version_path = plugin_src_path / "_version.py"
metadata_template = Path(__file__).parent / "metadata_template.json"

# Delete build and recreate
try:
    shutil.rmtree(build_path)
except FileNotFoundError:
    pass
os.makedirs(build_path / "plugin")
os.makedirs(build_path / "plugin" / "resources")

# Copy plugin. Sym-links doesn't work on Windows, that would've been easier
shutil.copytree(plugin_src_path / "dialog", build_path / "plugin" / "plugins" / "dialog")
shutil.copy(plugin_src_path / "__init__.py", build_path / "plugin" / "plugins" / "__init__.py")
shutil.copy(plugin_src_path / "board2pdf_action.py", build_path / "plugin" / "plugins" / "board2pdf_action.py")
shutil.copy(resources_path / "icon.png", build_path / "plugin" / "plugins" / "icon.png")
shutil.copy(resources_path / "icon-64x64.png", build_path / "plugin" / "resources" / "icon.png")
shutil.copy(repo_path / "README.md", build_path / "plugin" / "plugins" / "README.md")
shutil.copy(repo_path / "LICENSE", build_path / "plugin" / "plugins" / "LICENSE")
shutil.copytree(board2pdf_src_path / "pypdf", build_path / "plugin" / "plugins" / "pypdf")
shutil.copy(board2pdf_src_path / "cli.py", build_path / "plugin" / "plugins" / "board2pdf-cli.py")
shutil.copy(board2pdf_src_path / "default_config.ini", build_path / "plugin" / "plugins" / "default_config.ini")
shutil.copy(board2pdf_src_path / "persistence.py", build_path / "plugin" / "plugins" / "persistence.py")
shutil.copy(board2pdf_src_path / "plot.py", build_path / "plugin" / "plugins" / "plot.py")
shutil.copy(version_path, build_path / "plugin" / "plugins" / "_version.py")

# Clean out any __pycache__ or .pyc files (https://stackoverflow.com/a/41386937)
[p.unlink() for p in build_path.rglob("*.py[co]")]
[p.rmdir() for p in build_path.rglob("__pycache__")]

# Don't include test_dialog.py. It isn't needed. It's a developer thing.
[p.unlink() for p in build_path.rglob("test_dialog.py")]

# Copy metadata
metadata = build_path / "plugin" / "metadata.json"
shutil.copy(metadata_template, metadata)

# Load up json script
with metadata.open("r") as f:
    md = json.load(f)

# Get version from resource/_version.py
# https://stackoverflow.com/a/7071358

verstrline = version_path.open("rt").read()
VSRE = r"^__version__ = ['\"]([^'\"]*)['\"]"
mo = re.search(VSRE, verstrline, re.M)
if mo:
    verstr = mo.group(1)
else:
    verstr = "1.0.0"

# Update download URL
md["versions"][0].update(
    {
        "version": verstr,
        "download_url": "https://gitlab.com/dennevi/kicad-plugins-releases/-/raw/main/Board2Pdf/releases/Board2Pdf_v{0}.zip".format(
            verstr
        ),
    }
)

# Update metadata.json
with metadata.open("w") as of:
    json.dump(md, of, indent=2)

# Zip all files

pcm_name = "releases/Board2Pdf_v{0}".format(md["versions"][0]["version"])
pcm_path = build_path / pcm_name
zip_file = shutil.make_archive(pcm_path, "zip", build_path / "plugin")

# Rename the plugin directory so we can upload it as an artifact - and avoid the double-zip
shutil.move(build_path / "plugin", pcm_path)
