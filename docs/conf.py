from __future__ import annotations

import pathlib
import sys

sys.path.append(str(pathlib.Path(__file__).parent))

extensions = [
    "sphinx_immaterial",
]

html_theme = "sphinx_immaterial"
html_static_path = ["_static"]
html_css_files = ["css/extra.css"]

html_theme_options = {
    "repo_url": "https://github.com/delfick/pr-change-tracker",
    "features": ["toc.integrate", "navigation.tabs", "navigation.tabs.sticky"],
}

exclude_patterns = ["_build/**", ".sphinx-build/**", "README.rst"]

master_doc = "index"
source_suffix = ".rst"

pygments_style = "pastie"

copyright = "delfick"
project = "pr-change-tracker"

version = "0.1"
release = "0.1"

autodoc_preserve_defaults = True
