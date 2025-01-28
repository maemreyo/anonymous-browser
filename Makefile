# Python interpreter
PYTHON := python3
VENV := venv
PIP := $(VENV)/bin/pip

# Project directories
BUILD_DIR := build
DIST_DIR := dist
EGG_INFO := *.egg-info

# Default target
.DEFAULT_GOAL := help

.PHONY: help
help:
	@echo "Available commands:"
	@echo "  make setup    - Create virtual environment and install dependencies"
	@echo "  make build    - Build the project"
	@echo "  make install  - Install the built package"
	@echo "  make test     - Run tests"
	@echo "  make clean    - Clean build artifacts"
	@echo "  make run      - Run the application"

.PHONY: setup
setup:
	$(PYTHON) -m venv $(VENV)
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt

.PHONY: build
build: clean
	$(PYTHON) setup.py build
	$(PYTHON) setup.py sdist bdist_wheel

.PHONY: install
install: build
	$(PIP) install -e .

.PHONY: test
test:
	$(PYTHON) -m pytest tests/

.PHONY: clean
clean:
	rm -rf $(BUILD_DIR)
	rm -rf $(DIST_DIR)
	rm -rf $(EGG_INFO)
	rm -rf __pycache__
	rm -rf .pytest_cache
	rm -rf .coverage
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.pyd" -delete
	find . -type f -name ".coverage" -delete
	find . -type f -name "coverage.xml" -delete
	find . -type f -name ".pytest_cache" -delete

.PHONY: run
run:
	PYTHONPATH=. python3 src/main.py

.PHONY: setup-browsers
setup-browsers:
	$(VENV)/bin/playwright install

.PHONY: dev
dev: setup install setup-browsers
	$(PIP) install -r requirements-dev.txt

# Additional targets can be added based on project needs
.PHONY: lint
lint:
	$(PYTHON) -m flake8 src/ tests/
	$(PYTHON) -m black src/ tests/ --check
	$(PYTHON) -m isort src/ tests/ --check-only

.PHONY: format
format:
	$(PYTHON) -m black src/ tests/
	$(PYTHON) -m isort src/ tests/

# Freeze current dependencies
freeze:
	pip freeze > requirements.txt

# Freeze only direct dependencies (recommended)
freeze-direct:
	pip install pipdeptree
	pipdeptree -f --warn silence | grep -E '^[a-zA-Z0-9\-]+' > requirements.txt