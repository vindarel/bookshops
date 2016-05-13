pip:
	pip install -r requirements.txt

npm:
	npm install

install: pip npm

decitre:
	@cd frFR/decitre/ && python test_end2end.py

librairiedeparis:
	@cd frFR/librairiedeparis/ && python test_end2end.py

casadellibro:
	@cd esES/casadellibro/ && python test_end2end.py

germanscraper:
	@cd bookshops/deDE/buchlentner/ && python test_end2end.py

testscrapers: decitre casadellibro librairiedeparis

build:
	# build a source distribution
	python setup.py sdist
	# build a pure python wheel (built package)
	python setup.py bdist_wheel

upload-pypi:
	# hint: doesn't work with the old tar.gz in dist/
	twine upload dist/*
