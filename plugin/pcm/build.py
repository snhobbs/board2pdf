import os
import shutil
from pathlib import Path
import json
import re

src_path = (Path(__file__).parent.parent / "src").absolute()
version_path = src_path / "_version.py"

metadata_template = Path(__file__).parent / "metadata_template.json"
build_path = Path("build").absolute()

icons_path = src_path.parent / "icons"
resources_path = icons_path

# Delete build and recreate
try:
    shutil.rmtree(build_path)
except FileNotFoundError:
    pass
os.makedirs(build_path / "plugin")
os.makedirs(build_path / "plugin" / "resources")

# Copy plugin
shutil.copytree(src_path, build_path / "plugin" / "plugins")
shutil.copy(
    icons_path / "icon-64x64.png", build_path / "plugin" / "resources" / "icon.png"
)

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
