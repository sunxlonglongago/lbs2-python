.DEFAULT_GOAL := help

SHELL := /bin/bash

V ?= 0
Q := $(if $(filter 1 true yes,$(V)),,@)

ROOT_DIR := $(abspath .)
FRONTEND_DIR := $(ROOT_DIR)/frontend
SERVER_SRC_DIR := $(ROOT_DIR)/server/src
SERVER_STATIC_DIR := $(SERVER_SRC_DIR)/static
DEV_DATA_DIR ?= $(ROOT_DIR)/dev-data

PORT ?= 5059
SERVICE ?= lbs
RELEASE_DIR ?= /data/release/lbs
SERVER_DIR := $(RELEASE_DIR)/server
DATA_DIR := $(RELEASE_DIR)/data
SUDO ?= sudo
# Service account written into the systemd unit; defaults to the current user.
RUN_USER ?= $(shell if [ -n "$$SUDO_USER" ] && [ "$$SUDO_USER" != "root" ]; then printf '%s' "$$SUDO_USER"; else id -un; fi)
RUN_GROUP ?= $(shell if [ -n "$$SUDO_USER" ] && [ "$$SUDO_USER" != "root" ]; then id -gn "$$SUDO_USER"; else id -gn; fi)

# Only treat DATA_DIR as the E2E data source when it is set on the command line;
# otherwise the API E2E run creates its own temporary directory.
ifeq ($(origin DATA_DIR), command line)
  E2E_DATA_DIR := $(DATA_DIR)
endif

PYTHON ?= python3
UV ?= $(shell command -v uv 2>/dev/null || echo uv)
UV_RUN := $(UV) run --project "$(SERVER_SRC_DIR)" --no-sync python

.PHONY: help build fe dev server_dev install install_dirs install_source install_deps \
	update service-install service-status service-logs test_api_full db-import db-seed \
	db-schema docs clean

help:  ## List all targets
	$(Q)printf '\nLBS^2\n\n'
	$(Q)grep -hE '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
		| awk 'BEGIN {FS = ":.*?## "} {printf "  \033[36m%-16s\033[0m %s\n", $$1, $$2}'
	$(Q)printf '\n'

build: fe  ## Build the frontend (same as make fe)

fe:  ## Copy frontend/ into server/src/static/
	$(Q)rm -rf "$(SERVER_STATIC_DIR)"
	$(Q)mkdir -p "$(SERVER_STATIC_DIR)"
	$(Q)cp -R "$(FRONTEND_DIR)/." "$(SERVER_STATIC_DIR)/"
	$(Q)echo '==> frontend synced to server/src/static'

dev: server_dev  ## Run the local development server

server_dev:  ## Run Flask against the dev-data/ directory
	$(Q)mkdir -p "$(DEV_DATA_DIR)"
	$(Q)$(PYTHON) "$(SERVER_SRC_DIR)/tools/import_access.py" --data "$(DEV_DATA_DIR)" || true
	$(Q)$(PYTHON) "$(SERVER_SRC_DIR)/tools/seed_demo.py" --data "$(DEV_DATA_DIR)"
	$(Q)printf '==> http://127.0.0.1:%s/\n' "$(PORT)"
	$(Q)SESSION_COOKIE_SECURE=0 $(PYTHON) "$(SERVER_SRC_DIR)/app.py" --data "$(DEV_DATA_DIR)" --port $(PORT)

db-import:  ## Import the original Access databases into dev-data/
	$(PYTHON) "$(SERVER_SRC_DIR)/tools/import_access.py" --data "$(DEV_DATA_DIR)"

db-seed:  ## Write the hello world demo rows
	$(PYTHON) "$(SERVER_SRC_DIR)/tools/seed_demo.py" --data "$(DEV_DATA_DIR)"

db-schema:  ## Verify the SQLite schema against the Access reference
	$(PYTHON) "$(SERVER_SRC_DIR)/tools/dump_schema.py" --data "$(DEV_DATA_DIR)"

docs:  ## Regenerate docs/database.md, docs/api.md and docs/openapi.json
	$(Q)$(PYTHON) "$(SERVER_SRC_DIR)/tools/export_docs.py"
	$(Q)$(PYTHON) "$(SERVER_SRC_DIR)/export_openapi.py"

install: install_dirs install_source install_deps  ## Install into RELEASE_DIR

install_dirs:
	$(Q)$(SUDO) mkdir -p "$(SERVER_DIR)" "$(DATA_DIR)"
	$(Q)if [ "$$(id -u)" = "0" ] && [ -n "$$SUDO_USER" ]; then \
		$(SUDO) chown -R "$$SUDO_USER" "$(RELEASE_DIR)"; fi
	$(Q)echo '==> directories ready: $(RELEASE_DIR)'

install_source: fe  ## Copy the source and static output into the release directory
	$(Q)$(SUDO) rm -rf "$(SERVER_DIR)"
	$(Q)$(SUDO) mkdir -p "$(SERVER_DIR)"
	$(Q)$(SUDO) cp -R "$(SERVER_SRC_DIR)/." "$(SERVER_DIR)/"
	$(Q)if [ "$$(id -u)" = "0" ] && [ -n "$$SUDO_USER" ]; then \
		$(SUDO) chown -R "$$SUDO_USER" "$(SERVER_DIR)"; fi
	$(Q)echo '==> source installed to $(SERVER_DIR)'

install_deps:  ## Sync the Python dependencies
	$(Q)cd "$(SERVER_SRC_DIR)" && $(UV) sync --frozen 2>/dev/null || \
		cd "$(SERVER_SRC_DIR)" && $(UV) sync
	$(Q)echo '==> dependencies synced'

update: install_source  ## Refresh the release directory without touching data
	$(Q)echo '==> updated; restart with: sudo systemctl restart $(SERVICE)'

service-install:  ## Install and enable the systemd service
	$(Q)sed -e 's#^User=.*#User=$(RUN_USER)#' \
		-e 's#^Group=.*#Group=$(RUN_GROUP)#' \
		-e 's#^WorkingDirectory=.*#WorkingDirectory=$(SERVER_DIR)#' \
		-e 's#--data [^ ]*#--data $(DATA_DIR)#' \
		-e 's#^ReadWritePaths=.*#ReadWritePaths=$(DATA_DIR)#' \
		-e 's#^ReadOnlyPaths=.*#ReadOnlyPaths=$(SERVER_DIR)/static#' \
		"$(SERVER_SRC_DIR)/deploy/$(SERVICE).service" \
		| $(SUDO) tee "/etc/systemd/system/$(SERVICE).service" >/dev/null
	$(Q)$(SUDO) chmod 0644 "/etc/systemd/system/$(SERVICE).service"
	$(Q)$(SUDO) systemctl daemon-reload
	$(Q)$(SUDO) systemctl enable --now "$(SERVICE)"

service-status:  ## Show the service status
	$(Q)systemctl status "$(SERVICE)" --no-pager

service-logs:  ## Follow the service log
	$(Q)journalctl -u "$(SERVICE)" -f

test_api_full:  ## Run the full business API end-to-end suite
	$(Q)$(PYTHON) "$(ROOT_DIR)/server/tests/api_full_e2e.py" \
		$(if $(E2E_DATA_DIR),--data-dir "$(E2E_DATA_DIR)",)

clean:  ## Remove build output and development data
	$(Q)rm -rf "$(SERVER_STATIC_DIR)" "$(DEV_DATA_DIR)"
	$(Q)$(MAKE) -C "$(ROOT_DIR)/server" clean
