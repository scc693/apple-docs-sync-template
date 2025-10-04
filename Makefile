.PHONY: docs-sync
docs-sync:
	@bash scripts/sync_apple_docs.sh

.PHONY: docs-config
docs-config:
	@python scripts/generate_docs_config.py
