pip:
	pip install -r requirements.txt

install: pip 

decitre:
	@cd bookshops/frFR/decitre/ && python test_end2end.py

librairiedeparis:
	@cd bookshops/frFR/librairiedeparis/ && python test_end2end.py

frenchscrapers: librairiedeparis decitre

frenchscraper: librairiedeparis

casadellibro:
	@cd bookshops/esES/casadellibro/ && python test_end2end.py

spanishscraper: casadellibro

germanscraper:
	@cd bookshops/deDE/buchlentner/ && python test_end2end.py

movies:
	@cd bookshops/all/momox/ && python test_end2end.py

testscrapers: spanishscraper germanscraper librairiedeparis movies

build:
	# build a source distribution
	python setup.py sdist
	# build a pure python wheel (built package)
	python setup.py bdist_wheel

upload-pypi:
	# hint: doesn't work with the old tar.gz in dist/
	twine upload dist/*
