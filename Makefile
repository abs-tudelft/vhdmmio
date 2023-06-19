# This makefile just has a few shorthands in it. The real "buildsystem" is
# Python setuptools (setup.py).

.PHONY: all
all: examples doc test lint

.PHONY: examples
examples:
	$(MAKE) -C examples

.PHONY: doc
doc:
	rm -rf doc/md doc/html
	mkdir -p doc/md doc/html
	python3 -m vhdmmio.config doc/md
	-cd doc && mdbook build

.PHONY: test
test:
	pytest

.PHONY: lint-all
lint-all:
	pylint vhdmmio --rcfile .pylintrc

.PHONY: lint-check
lint-check:
	pylint vhdmmio --rcfile .pylintrc --disable=R,C,W
