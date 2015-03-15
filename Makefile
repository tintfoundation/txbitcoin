test:
	trial txbitcoin

lint:
	pep8 --ignore=E303,E251,E201,E202 ./txbitcoin --max-line-length=140
	find ./txbitcoin -name '*.py' | xargs pyflakes

install:
	python setup.py install
