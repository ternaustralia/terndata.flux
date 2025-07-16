import packaging.version

# from pallets_sphinx_themes import get_version
# from pallets_sphinx_themes import ProjectLink

# TODO: may need to add project source code to sys.path here so that auto-doc works


# Project --------------------------------------------------------------

project = "terndata.flux"
copyright = "tern"
author = "tern"
#release, version = version, version  # TODO release is meant to be short version of version

# General --------------------------------------------------------------

master_doc = "index"
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.intersphinx",
    "sphinx.ext.napoleon",
    "sphinx.ext.todo",
    "sphinxcontrib.openapi",
    # "sphinxcontrib.log_cabinet",
    # "pallets_sphinx_themes",
    # "sphinx_issues",
    # "sphinx_tabs.tabs",
    "sphinx_rtd_theme",
    "sphinx_github_changelog",
]

intersphinx_mapping = {
    "python": ("https://docs.python.org/3/", None),
    "werkzeug": ("https://werkzeug.palletsprojects.com/", None),
    "netCDF4": ("https://unidata.github.io/netcdf4-python/", None),
    "xarray": ("https://docs.xarray.dev/en/stable/", None),
    "numpy": ("https://numpy.org/doc/stable/", None),
    "pandas": ("https://pandas.pydata.org/docs/", None),
    "authlib": ("https://docs.authlib.org/en/stable/", None),
    "itsdangerous": ("https://itsdangerous.palletsprojects.com/", None),
    "pytest": ("https://docs.pytest.org/en/latest/", None),
}
# issues_github_path = "pallets/flask"

todo_include_todos = True

autodoc_default_options = {
    "member-order": "bysource",
}
autodoc_typehints = "both"  # "none", "both", "signature", "description"

# HTML -----------------------------------------------------------------

html_theme = "sphinx_rtd_theme"
html_theme_options = {
    # Toc options
    "collapse_navigation": True,
    "sticky_navigation": True,
    "navigation_depth": 4,
    "includehidden": True,
    "titles_only": False,
    "prev_next_buttons_location": "both",
}
html_context = {
    "display_github": True,  # Integrate Github
    "github_user": "ternaustralia",  # Username
    "github_repo": "terndata.flux",  # Repo name
    "github_version": "main",  # Version
    "conf_py_path": "/docs/",  # Path in the checkout to the docs root
}
# html_static_path = ["_static"]
# html_favicon = "_static/flask-icon.png"
# html_logo = "_static/flask-icon.png"
#html_title = f"terndata.flux Documentation ({version})"
html_show_sourcelink = False

# LaTeX ----------------------------------------------------------------

#latex_documents = [(master_doc, f"Flask-{version}.tex", html_title, author, "manual")]

# Local Extensions -----------------------------------------------------


# def github_link(name, rawtext, text, lineno, inliner, options=None, content=None):
#     app = inliner.document.settings.env.app
#     release = app.config.release
#     base_url = "https://github.com/pallets/flask/tree/"

#     if text.endswith(">"):
#         words, text = text[:-1].rsplit("<", 1)
#         words = words.strip()
#     else:
#         words = None

#     if packaging.version.parse(release).is_devrelease:
#         url = f"{base_url}master/{text}"
#     else:
#         url = f"{base_url}{release}/{text}"

#     if words is None:
#         words = url

#     from docutils.nodes import reference
#     from docutils.parsers.rst.roles import set_classes

#     options = options or {}
#     set_classes(options)
#     node = reference(rawtext, words, refuri=url, **options)
#     return [node], []


# def setup(app):
#     app.add_role("gh", github_link)
