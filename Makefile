.PHONY: setup backend frontend

setup:
	chmod +x setup.sh && ./setup.sh

backend:
	cd backend && PYTHONPATH=src uvicorn studylens.main:app --reload

frontend:
	cd frontend && npm run dev
