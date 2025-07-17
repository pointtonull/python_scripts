SRC = $(PWD)/src
TESTS = $(PWD)/tests

PYTHON = python3
REQUIREMENTS = $(SRC)/requirements.txt
STAGE = dev

.PHONY: unit test coverage clean tdd debug

deps: .deps
.deps: $(REQUIREMENTS) requirements.txt
	pip install -r requirements.txt
	pip install -r $(REQUIREMENTS)
	touch .deps

clean:
	@echo "Cleaning all artifacts..."
	@-rm -rf _build
	@-rm -rf _temp
	@-rm .deps

ipython: deps
	$(PYTHON) -m IPython

unit test: deps
	$(PYTHON) -m pytest $(ARGS) $(TESTS)

tdd: deps ## run tests on filesystem events
	$(PYTHON) -m pytest_watch $(SRC) $(TESTS) \
		--runner "$(PYTHON) -m pytest $(ARGS) --stepwise $(TESTS) --show-capture=no --tb=long --showlocals"

debug: deps ## run tests on filesystem events, open pdb on failures
	ptw $(SRC) $(TESTS) --pdb --runner "$(PYTHON) -m pytest $(ARGS) --stepwise $(TESTS)"

coverage: deps
	$(PYTHON) -m pytest tests $(ARGS) --cov $(SRC) --cov-report=term-missing:skip-covered tests
