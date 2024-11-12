# Bump Version
This will update the patch version in all the required spots. 
The plugin/pcm/metadata_template.json and plugin/src/_version.py need to be the same and src/board2pdf/_version.py and pyproject.toml need to be the same. The plugin and libray do not need to have matching versions.

```sh
bumpversion --current-version {CURRENT VERSION} patch plugin/pcm/metadata_template.json src/board2pdf/_version.py plugin/src/_version.py pyproject.toml
```

# KiCad Plugin

## Install
To install the KiCad Plugin from the cloned repo:
+ Open the Scripting Console within KiCad PCB Editor.
+ Set the board2pdf_path variable to the path of your cloned repo:
```sh
board2pdf_path = "C:\\git\\other-repos\\Board2Pdf"
```
+ Run this command to run a script that copies all files to the correct place, and then starts the plugin:
```sh
exec(open(board2pdf_path+"\\plugin\\install_and_launch.py").read())
```
+ If you make changes to the source code in the repo, you only need to run the second command again to try out your changes.

## Build KiCad Plugin
+ Run the build script:
```sh
cd plugin
python3 pcm/build.py
```
+ This puts our new PCM compatible zip in /pcm/build/. This can be installed manually in PCM, or be deployed to PCM for everyone to be able to install it.

## Deploying Plugin in PCM
+ Upload the zip created in the previous step
+ The package validity can be checked with (git@gitlab.com:kicad/addons/metadata.git)
+ The various integrity stats should be integrated with their CI tools

Follow these instructions: https://gitlab.com/kicad/addons/metadata

# PIP Package
This projects pyproject.toml is using setuptools as the build tool.

Read this article for instructions to upload to pypi
https://packaging.python.org/en/latest/guides/distributing-packages-using-setuptools/

## Install
+ To install a the Python Packages from the cloned repo, simply run:

```sh
pip install .
```
Don't miss the dot at the end!!

## Build
+ To build a package for redistribution run:

```sh
python3 -m build --sdist
```

This will create dist/board2pdf-{VERSION}.tar.gz

## Check Build

```sh
twine check dist/*
```