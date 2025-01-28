# Python interpreter
PYTHON := python3
VENV := venv
PIP := $(VENV)/bin/pip
PYTEST := $(VENV)/bin/pytest

# Project directories
BUILD_DIR := build
DIST_DIR := dist
EGG_INFO := *.egg-info
TEST_DIR := tests
SRC_DIR := src

# Test configuration
PYTEST_ARGS := -v -s --show-capture=all
COVERAGE_ARGS := --cov=$(SRC_DIR) --cov-report=term-missing --cov-report=html --cov-report=xml

# Colors for terminal output
CYAN := \033[0;36m
GREEN := \033[0;32m
RED := \033[0;31m
YELLOW := \033[0;33m
NC := \033[0m # No Color

# Default target
.DEFAULT_GOAL := help

.PHONY: help
help:
	@echo "$(CYAN)Available commands:$(NC)"
	@echo "  $(GREEN)make setup$(NC)         - Create virtual environment and install dependencies"
	@echo "  $(GREEN)make build$(NC)         - Build the project"
	@echo "  $(GREEN)make install$(NC)       - Install the built package"
	@echo "  $(GREEN)make clean$(NC)         - Clean build artifacts"
	@echo "  $(GREEN)make run$(NC)           - Run the application"
	@echo ""
	@echo "$(CYAN)Testing commands:$(NC)"
	@echo "  $(GREEN)make test$(NC)          - Run all tests"
	@echo "  $(GREEN)make test-unit$(NC)     - Run only unit tests"
	@echo "  $(GREEN)make test-integration$(NC) - Run only integration tests"
	@echo "  $(GREEN)make test-coverage$(NC) - Run tests with coverage report"
	@echo "  $(GREEN)make test-watch$(NC)    - Run tests in watch mode"
	@echo ""
	@echo "$(CYAN)Development commands:$(NC)"
	@echo "  $(GREEN)make lint$(NC)          - Run linting checks"
	@echo "  $(GREEN)make format$(NC)        - Format code"
	@echo "  $(GREEN)make dev$(NC)           - Setup development environment"

.PHONY: setup
setup:
	@echo "$(CYAN)Creating virtual environment...$(NC)"
	$(PYTHON) -m venv $(VENV)
	@echo "$(CYAN)Upgrading pip...$(NC)"
	$(PIP) install --upgrade pip
	@echo "$(CYAN)Installing dependencies...$(NC)"
	$(PIP) install -r requirements.txt
	@echo "$(GREEN)Setup completed successfully!$(NC)"

# Test targets
.PHONY: test
test:
	@echo "$(CYAN)Running all tests...$(NC)"
	$(PYTHONPATH) $(PYTEST) $(PYTEST_ARGS) $(TEST_DIR)

.PHONY: test-unit
test-unit:
	@echo "$(CYAN)Running unit tests...$(NC)"
	$(PYTHONPATH) $(PYTEST) $(PYTEST_ARGS) $(TEST_DIR)/unit

.PHONY: test-integration
test-integration:
	@echo "$(CYAN)Running integration tests...$(NC)"
	$(PYTHONPATH) $(PYTEST) $(PYTEST_ARGS) $(TEST_DIR)/integration

.PHONY: test-coverage
test-coverage:
	@echo "$(CYAN)Running tests with coverage...$(NC)"
	$(PYTHONPATH) $(PYTEST) $(PYTEST_ARGS) $(COVERAGE_ARGS) $(TEST_DIR)
	@echo "$(GREEN)Coverage report generated in htmlcov/index.html$(NC)"

.PHONY: test-watch
test-watch:
	@echo "$(CYAN)Running tests in watch mode...$(NC)"
	$(PYTHONPATH) $(PYTEST) $(PYTEST_ARGS) --watch $(TEST_DIR)

# Development targets
.PHONY: lint
lint:
	@echo "$(CYAN)Running flake8...$(NC)"
	$(PYTHON) -m flake8 $(SRC_DIR) $(TEST_DIR)
	@echo "$(CYAN)Running black check...$(NC)"
	$(PYTHON) -m black $(SRC_DIR) $(TEST_DIR) --check
	@echo "$(CYAN)Running isort check...$(NC)"
	$(PYTHON) -m isort $(SRC_DIR) $(TEST_DIR) --check-only

.PHONY: format
format:
	@echo "$(CYAN)Formatting with black...$(NC)"
	$(PYTHON) -m black $(SRC_DIR) $(TEST_DIR)
	@echo "$(CYAN)Sorting imports with isort...$(NC)"
	$(PYTHON) -m isort $(SRC_DIR) $(TEST_DIR)
	@echo "$(GREEN)Code formatting completed!$(NC)"

.PHONY: clean
clean:
	@echo "$(CYAN)Cleaning build artifacts...$(NC)"
	rm -rf $(BUILD_DIR)
	rm -rf $(DIST_DIR)
	rm -rf $(EGG_INFO)
	rm -rf __pycache__
	rm -rf .pytest_cache
	rm -rf .coverage
	rm -rf htmlcov
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.pyd" -delete
	find . -type f -name ".coverage" -delete
	find . -type f -name "coverage.xml" -delete
	find . -type f -name ".pytest_cache" -delete
	@echo "$(GREEN)Clean completed!$(NC)"

.PHONY: run
run:
	@echo "$(CYAN)Running application...$(NC)"
	PYTHONPATH=. $(PYTHON) src/main.py

.PHONY: setup-browsers
setup-browsers:
	@echo "$(CYAN)Installing browsers for Playwright...$(NC)"
	$(VENV)/bin/playwright install

.PHONY: dev
dev: setup install setup-browsers
	@echo "$(CYAN)Installing development dependencies...$(NC)"
	$(PIP) install -r requirements-dev.txt
	@echo "$(GREEN)Development environment setup completed!$(NC)"

# Install required test dependencies
.PHONY: install-test-deps
install-test-deps:
	@echo "$(CYAN)Installing test dependencies...$(NC)"
	$(PIP) install pytest pytest-asyncio pytest-cov pytest-watch pytest-xdist

# Run tests in parallel
.PHONY: test-parallel
test-parallel:
	@echo "$(CYAN)Running tests in parallel...$(NC)"
	$(PYTEST) $(PYTEST_ARGS) -n auto $(TEST_DIR)

# Generate test report
.PHONY: test-report
test-report: test-coverage
	@echo "$(CYAN)Generating test report...$(NC)"
	$(PYTEST) $(PYTEST_ARGS) $(COVERAGE_ARGS) --html=report.html $(TEST_DIR)
	@echo "$(GREEN)Test report generated in report.html$(NC)"

# Quick test (faster execution for development)
.PHONY: test-quick
test-quick:
	@echo "$(CYAN)Running quick tests...$(NC)"
	$(PYTEST) $(PYTEST_ARGS) -m "not slow" $(TEST_DIR)


# Install development mode
.PHONY: install-dev
install-dev:
	@echo "$(CYAN)Installing package in development mode...$(NC)"
	$(PIP) install -e .
	@echo "$(GREEN)Development installation completed!$(NC)"

# Update dev target to include install-dev
.PHONY: dev
dev: setup install-dev setup-browsers
	@echo "$(CYAN)Installing development dependencies...$(NC)"
	$(PIP) install -r requirements-dev.txt
	@echo "$(GREEN)Development environment setup completed!$(NC)"