# Library / Package
This projects pyproject.toml is using setuptools as the build tool.

Read this article for instructions to upload to pypi
https://packaging.python.org/en/latest/guides/distributing-packages-using-setuptools/

## Bump Version
This will update the patch version in all the required spots. 
The plugin/pcm/metadata_template.json and plugin/src/_version.py need to be the same and src/board2pdf/_version.py and pyproject.toml need to be the same. The plugin and libray do not need to have matching versions.

```sh
bumpversion --current-version {CURRENT VERSION} patch plugin/pcm/metadata_template.json src/board2pdf/_version.py plugin/src/_version.py pyproject.toml
```

## Build

```sh
python3 -m build --sdist
```
This will create dist/board2pdf-{VERSION}.tar.gz

## Check Build

```sh
twine check dist/*
```

# Plugin / PCM
The instructions on how to build the PCM are in the pcm directory in the README.
Read the docs for more: https://gitlab.com/kicad/addons/metadata#recommended-workflow
