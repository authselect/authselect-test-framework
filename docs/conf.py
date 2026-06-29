# Configuration file for the Sphinx documentation builder.

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.abspath(".."))
sys.path.insert(0, os.path.abspath("."))

project = "authselect-test-framework"

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.intersphinx",
    "sphinx_design",
    "extensions.directives.TopologyMark",
]

exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

html_theme = "sphinx_rtd_theme"

autoclass_content = "both"
autodoc_default_options = {
    "members": True,
    "member-order": "bysource",
    "special-members": "__call__",
    "undoc-members": True,
    "inherited-members": False,
    "show-inheritance": True,
}

intersphinx_mapping = {
    "pytest_mh": ("https://pytest-mh.readthedocs.io/en/latest", None),
}
