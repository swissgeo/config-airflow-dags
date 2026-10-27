# Commands
UV_RUN := uv run
ALEMBIC := $(UV_RUN) alembic

.PHONY: db-revision
db-revision: ## Create a migration from model changes, e.g. make db-revision m="add process table"
	$(ALEMBIC) revision --autogenerate -m "$(m)"


.PHONY: db-upgrade
db-upgrade: ## Apply all pending migrations
	$(ALEMBIC) upgrade head


.PHONY: db-downgrade
db-downgrade: ## Revert the last migration
	$(ALEMBIC) downgrade -1


.PHONY: db-history
db-history: ## Show migration history
	$(ALEMBIC) history


.PHONY: db-check
db-check: ## Check that the migrations are in sync with the models (requires a running database)
	$(ALEMBIC) check


.PHONY: help
help: ## Display this help
# automatically generate the help page based on the documentation after each make target
# from https://gist.github.com/prwhite/8168133
	@awk 'BEGIN {FS = ":.*##"} \
	/^[a-zA-Z0-9_.-]+:.*##/ { printf "%-15s %s\n", $$1, $$2 }' $(MAKEFILE_LIST) \
	| sort \
	| awk 'BEGIN { printf "\nUsage:\n  make \033[36m<target>\033[0m\n\n" } \
	{ printf "  \033[36m%-15s\033[0m %s\n", $$1, substr($$0, index($$0,$$2)) }'
