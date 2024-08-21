"""
Configuration file for the Sphinx documentation builder.

For the full list of built-in configuration values, see the documentation:
https://www.sphinx-doc.org/en/master/usage/configuration.html

-- Project information -----------------------------------------------------
https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information
"""

project = "Github App Handler"
copyright = "2024, Heitor Polidoro"
author = "Heitor Polidoro"

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "myst_parser",
    "sphinx.ext.autodoc",
    "autodoc2",
    # "sphinx.ext.intersphinx",
    # "sphinx.ext.viewcode",
    # "sphinxcontrib.bibtex",
    #    "sphinx_panels",
    # "sphinxext.rediraffe",
    # "sphinxcontrib.mermaid",
    # "sphinxext.opengraph",
]
myst_enable_extensions = ["colon_fence"]

# Autodoc2 Configuration
autodoc2_render_plugin = "myst"
autodoc2_packages = ["../githubapp"]
autodoc2_hidden_objects = ["inherited", "dunder", "private"]
autodoc2_sort_names = True

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "sphinx_rtd_theme"
html_static_path = ["_static"]
