import os
from setuptools import setup, find_packages

def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

try:
    import pypandoc
    long_description = pypandoc.convert('README.md', 'rst')
except (IOError, OSError, ImportError):
    long_description = read('README.md')

setup(
    name = "bookshops",
    version = "0.2.0",
    packages = find_packages(exclude=["contrib", "doc", "tests"]),

    install_requires = [
        "requests==2.7",
        "requests_cache==0.4",
        "beautifulsoup4",
        "isbnlib<4", # useful tools to manipulate and get isbn
        "lxml==3.5", # parsing
        "toolz",     # functional utils
        "tabulate", 
        "addict",    # fancy dict access
        "termcolor", # colored print
        "unidecode", # string clean up 
        "distance",  # between two strings
        "clize==3",  # quick and easy cli args
        "tqdm",      # progress bar
        "termcolor", # terminal color
    ],

    package_data = {
        # If any package contains *.txt or *.rst files, include them:
        # '': ['*.txt', '*.rst'],
        # And include any *.msg files found in the 'hello' package, too:
        # 'hello': ['*.msg'],
    },

    # metadata for upload to PyPI
    author = "vindarel",
    author_email = "ehvince@mailz.org",
    description = "Get book information (isbn or search) from real bookstores.",
    long_description = long_description,
    license = "GNU LGPLv3",
    keywords = "bookshop bookstore library book isbn ean webscraping",
    url = "https://gitlab.com/vindarel/bookshops",

    entry_points = {
        "console_scripts": [
            "livres = bookshops.frFR.librairiedeparis.librairiedeparisScraper:run",
            "libros = bookshops.esES.casadellibro.casadellibroScraper:run",
            "bucher = bookshops.deDE.buchlentner.buchlentnerScraper:run",
        ],
    },

    tests_require = {

    },

    classifiers = [
        "Environment :: Web Environment",
        "Environment :: Console",
        "Environment :: Plugins",
        "Intended Audience :: Developers",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: GNU Library or Lesser General Public License (LGPL)",
        "Topic :: Utilities",
        "Programming Language :: Python :: 2.7",
        "Topic :: Internet",
        "Topic :: Software Development :: Libraries",
    ],

)
