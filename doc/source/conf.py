# -*- coding: utf-8 -*-

# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
import os
import sys
sys.path.append(os.path.abspath('../../'))
sys.path.append(os.path.abspath('../rpi_dummy_modules/'))
#import ohmpi  # import Ohmpi module to be documented in api.rst by numpydoc

import sphinx_rtd_theme


from shutil import copyfile
# -- Project information -----------------------------------------------------

project = 'OhmPi'
copyright = '2022-2024, the OhmPi Team.'
author = 'OhmPi Team'

# The full version, including alpha/beta/rc tags
release = 'v2024'


# -- General configuration ---------------------------------------------------


extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.coverage',
    'sphinx.ext.mathjax',
    'numpydoc',
    'recommonmark',
    'linuxdoc.rstFlatTable',
]



numpydoc_show_class_members = True


# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = []


# -- Options for HTML output -------------------------------------------------
html_logo = 'img/logo/ohmpi/LOGO_OHMPI.png'
# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
html_theme = 'sphinx_rtd_theme'
html_style = 'css/my_theme.css'
#html_theme = 'sphinxawesome_theme'
#html_theme = 'bootstrap'
#html_theme_path = sphinx_bootstrap_theme.get_html_theme_path()
#html_theme ='groundwork'
# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ['_static']


html_context = {
    "display_gitlab": True, # Integrate Gitlab
    "gitlab_repo": "ohmpi/ohmpi", # Repo name
    "gitlab_version": "master", # Version
    "conf_py_path": "/doc/source/", # Path in the checkout to the docs root
}


master_doc = 'index'
