#
# Copyright 2025-2026 Scott Gigawatt
#
# Licensed under the Apache License, Version 2.0.
#
# Makefile: Provide reproducible, safe repository checks without running utilities.
#

# Centralize developer paths and commands for local runs and CI.
PYTHON ?= python3
VENV := .venv
DEV_PYTHON = $(VENV)/bin/python
PRE_COMMIT = $(VENV)/bin/pre-commit
RUFF = $(VENV)/bin/ruff
NODE_BIN = node_modules/.bin

.DEFAULT_GOAL := help
.PHONY: help setup hooks check test test-precommit syntax lint format test-types spellcheck markdown

#
# help: Show the supported developer commands.
#
help:
	@printf '%s\n' 'make setup          Install locked developer tools (Python 3.11+, Node 22.18+).' 'make hooks          Install the pre-commit Git hook.' 'make check          Run all-file pre-commit checks and checker tests.' 'make test-precommit Run every hook against all repository files.' 'make test           Run isolated checker tests.' 'make syntax         Parse source and configuration without running utilities.' 'make lint           Check every Python source with Ruff.' 'make format         Apply Python formatting explicitly.' 'make test-types     Strictly type-check developer helpers and tests.' 'make spellcheck     Check text using the editor vocabulary.' 'make markdown       Lint every Markdown document.'

#
# setup: Install hash-verified Python tools and the integrity-locked Node tools.
#
setup:
	$(PYTHON) -c 'import sys; assert sys.version_info >= (3, 11), "Use Python 3.11 or newer; set PYTHON=python3.13 if needed."'
	$(PYTHON) -m venv $(VENV)
	$(DEV_PYTHON) -m pip install --disable-pip-version-check --require-hashes -r requirements-dev.txt
	npm ci --ignore-scripts --engine-strict

#
# hooks: Install the same checks used by pull-request validation.
# Dependencies:
#   setup - Install the pinned developer tools before installing hooks.
#
hooks:
	$(PRE_COMMIT) install

#
# check: Validate the complete repository and exercise checker safety.
# Dependencies:
#   test-precommit - Check source, secrets, spelling, and shared formatting policies.
#   test - Verify parsers and their no-execution contract in isolated fixtures.
#
check: test-precommit test

#
# test-precommit: Run every configured hook across the repository.
#
test-precommit:
	$(PRE_COMMIT) run --all-files --show-diff-on-failure

#
# test: Exercise only developer-checker fixtures, never the real utilities.
#
test:
	$(DEV_PYTHON) -m unittest discover -s tests -v

#
# syntax: Parse tracked and new sources allowed by Git ignore rules without executing them.
#
syntax:
	$(DEV_PYTHON) -m scripts.check_syntax

#
# lint: Enforce the shared Python correctness and import rules.
#
lint:
	$(RUFF) check .
	$(RUFF) format --check .

#
# format: Apply the shared Python formatter without changing runtime behavior.
#
format:
	$(RUFF) format .

#
# test-types: Enforce strict typing for developer helpers and their tests.
#
test-types:
	$(NODE_BIN)/pyright --pythonpath $(DEV_PYTHON) --warnings

#
# spellcheck: Use the same project vocabulary as the editor.
#
spellcheck:
	$(DEV_PYTHON) -m scripts.check_spelling

#
# markdown: Check all Markdown using the shared reference-repository style.
#
markdown:
	$(NODE_BIN)/markdownlint-cli2
