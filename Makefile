.PHONY: dev dev-backend dev-frontend

# Start both backend (FastAPI) and frontend (Vite) for local development.
# Uses uv for Python env and pnpm for web.
# Trap ensures both processes are killed on Ctrl-C.
dev:
	@echo "==> Starting VideoForge dev environment..."
	@trap 'echo "==> Shutting down..."; kill 0' EXIT; \
		uv run uvicorn videoforge.api.app:create_app --factory --reload --host 0.0.0.0 --port 8000 & \
		cd web && pnpm dev & \
		wait

# Python backend only
dev-backend:
	uv run uvicorn videoforge.api.app:create_app --factory --reload --host 0.0.0.0 --port 8000

# Web frontend only (proxy /api to localhost:8000)
dev-frontend:
	cd web && pnpm dev
