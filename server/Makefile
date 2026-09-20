.DEFAULT_GOAL := help

SHELL := /bin/bash

V ?= 0
Q := $(if $(filter 1 true yes,$(V)),,@)

SERVER_SRC_DIR := $(abspath src)

.PHONY: help clean

help:  ## List the server targets
	$(Q)printf '\nServer\n\n'
	$(Q)grep -hE '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
		| awk 'BEGIN {FS = ":.*?## "} {printf "  \033[36m%-14s\033[0m %s\n", $$1, $$2}'
	$(Q)printf '\n'

clean:  ## Remove the server caches
	$(Q)rm -rf \
		"$(SERVER_SRC_DIR)/.venv" \
		"$(SERVER_SRC_DIR)/__pycache__" \
		"$(SERVER_SRC_DIR)/tools/__pycache__" \
		"$(SERVER_SRC_DIR)/.pytest_cache" \
		"$(SERVER_SRC_DIR)/.ruff_cache"
	$(Q)find "$(SERVER_SRC_DIR)" -name '*.pyc' -delete 2>/dev/null || true
	$(Q)echo '==> server cleaned'
