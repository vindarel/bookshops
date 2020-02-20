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
    name="bookshops",
    version="0.6",
    packages=find_packages(exclude=["contrib", "doc", "tests"]),

    install_requires=[
        "pip",
        "requests==2.21",
        "beautifulsoup4",
        "isbnlib<4",  # useful tools to manipulate and get isbn
        "lxml==3.5",  # parsing
        # "html5lib==1.0b8",  # parsing.
        # WARN: newer version breaks bs4.
        # see https://bugs.launchpad.net/beautifulsoup/+bug/1603299
        "toolz",     # functional utils
        "tabulate",
        "addict",    # fancy dict access
        "termcolor",  # colored print
        "unidecode",  # string clean up
        "distance",  # between two strings
        "clize==3",  # quick and easy cli args
        "pyyaml==3.11",
        "tqdm",      # progress bar
        "termcolor",  # terminal color
    ],

    tests_require=[
        "twine",  # pypi upload
        "pypandoc",  # format the long description
    ],

    package_data={
        # If any package contains *.txt or *.rst files, include them:
        # '': ['*.txt', '*.rst'],
        # And include any *.msg files found in the 'hello' package, too:
        # 'hello': ['*.msg'],
    },

    # metadata for upload to PyPI
    author="vindarel",
    author_email="vindarel@mailz.org",
    description="Get book, dvd and cd information (isbn or search) from real bookstores.",  # noqa: E501
    long_description=long_description,
    license="GNU LGPLv3",
    keywords="bookshop bookstore library book dilicom dvd isbn ean ean13 webscraping",  # noqa: E501
    url="https://gitlab.com/vindarel/bookshops",

    entry_points={
        "console_scripts": [
            "livres = bookshops.frFR.librairiedeparis.librairiedeparisScraper:run",  # noqa: E501
            "dilicom = bookshops.frFR.dilicom.dilicomScraper:run",
            "lelivre = bookshops.frFR.lelivre.lelivreScraper:run",
            "libros = bookshops.esES.casadellibro.casadellibroScraper:run",
            "bucher = bookshops.deDE.buchlentner.buchlentnerScraper:run",
            "discogs = bookshops.all.discogs.discogsScraper:run",
            "movies = bookshops.all.momox.momox:run",
        ],
    },

    classifiers=[
        "Environment :: Web Environment",
        "Environment :: Console",
        "Environment :: Plugins",
        "Intended Audience :: Developers",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: GNU Library or Lesser General Public License (LGPL)",  # noqa: E501
        "Topic :: Utilities",
        "Programming Language :: Python :: 2.7",
        "Topic :: Internet",
        "Topic :: Software Development :: Libraries",
    ],

)
