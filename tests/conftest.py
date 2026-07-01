import os

# Some environments (Jupyter/ipykernel, certain CI runners) force FORCE_COLOR /
# CLICOLOR_FORCE onto every subprocess so tools like `ls`/`git` colorize nicely.
# Typer's Rich-based --help/version output then embeds ANSI escape codes,
# breaking plain substring assertions in CLI tests (e.g. "0.7.0" in result.output).
# Stripped here, once, before any test module (and its Typer app) is imported.
os.environ.pop("FORCE_COLOR", None)
os.environ.pop("CLICOLOR_FORCE", None)
