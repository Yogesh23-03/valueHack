.PHONY: test run

# Documented command: cd backend && pytest -q
test:
	pytest -q

run:
	uvicorn app.main:app --reload --port 8000
