
# To install Board2Pdf and start it, run these commands from the Scripting Console within KiCad PCB Editor:

# board2pdf_path = "C:\\{path to git repo}\\Board2Pdf"
# exec(open(board2pdf_path+"\\plugin\\install_and_launch.py").read())

# You must set board2pdf_path before executing the script, because the script doesn't know where it's located.
# You don't have to set board2pdf_path again if you run the script a second time.

import sys
import os
import shutil
import importlib
from pathlib import Path

# This is the path to where the plugin is installed for KiCad 8.0.
if os.name == 'nt': # If running Windows
    installed_path = Path(os.path.expanduser('~/Documents/KiCad/8.0/3rdparty/plugins/com_gitlab_dennevi_Board2Pdf')).absolute()
else: # If running Linux
    installed_path = Path(os.path.expanduser('~/.local/share/kicad/8.0/3rdparty/plugins/com_gitlab_dennevi_Board2Pdf/')).absolute()
#installed_path = Path("C:\\Users\\denne\\Documents\\KiCad\\8.0\\3rdparty\\plugins\\com_gitlab_dennevi_Board2Pdf").absolute()

repo_path = Path(board2pdf_path).absolute()
#repo_path = Path("C:\\git\\other-repos\\Board2Pdf").absolute()

# Delete the current installed plugin
try:
    shutil.rmtree(installed_path)
except FileNotFoundError:
    pass
except PermissionError:
    pass
    
try:
    os.makedirs(installed_path)
except FileExistsError:
    pass

# Build the plugin
os.chdir(repo_path / "plugin")
__file__ = repo_path / "plugin" / "pcm" / "build.py"
build_script_path = repo_path / "plugin" / "pcm" / "build.py"
print("Building Board2Pdf by executing", str(build_script_path))
exec(open(build_script_path).read())

# Find out which version was built
version_path = repo_path / "plugin" / "src" / "_version.py"
verstrline = version_path.open("rt").read()
VSRE = r"^__version__ = ['\"]([^'\"]*)['\"]"
mo = re.search(VSRE, verstrline, re.M)
if mo:
    verstr = mo.group(1)
else:
    print("Couldn't find the version in", str(version_path))

print("Version that was built:", verstr)

# Copy the new plugin to the path where it should be installed
build_path = Path(repo_path / "plugin" / "build" / "releases" / "Board2Pdf_v{0}".format(verstr) / "plugins").absolute()
print("Board2Pdf will be copied from:", build_path)
print("Board2Pdf will be copied to:", installed_path)

shutil.copytree(build_path, installed_path, dirs_exist_ok=True)

# Open plugin
print("Starting Board2Pdf")
sys.path.append(os.path.expanduser(installed_path))

try:
    importlib.reload(sys.modules['com_gitlab_dennevi_Board2Pdf._version'])
    importlib.reload(sys.modules['com_gitlab_dennevi_Board2Pdf.plot'])
    importlib.reload(sys.modules['com_gitlab_dennevi_Board2Pdf.dialog.dialog_base'])
    importlib.reload(sys.modules['com_gitlab_dennevi_Board2Pdf.dialog.settings_dialog'])
    importlib.reload(sys.modules['com_gitlab_dennevi_Board2Pdf.dialog'])
    importlib.reload(sys.modules['com_gitlab_dennevi_Board2Pdf.persistence'])
    importlib.reload(sys.modules['com_gitlab_dennevi_Board2Pdf.board2pdf_action'])
    importlib.reload(sys.modules['com_gitlab_dennevi_Board2Pdf'])
    importlib.reload(board2pdf_action)

except (NameError, KeyError):
    import board2pdf_action

board2pdf_action.main()