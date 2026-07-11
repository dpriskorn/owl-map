# OWL Map - FastAPI + Vue/Vite

api:
    poetry run uvicorn backend.main:app --reload --port 8080

vite:
    cd frontend && npx vite --port 3000

be-lint:
    poetry run ruff check backend/ matcher/

be-file-len:
    @find backend/ matcher/ -name "*.py" -exec wc -l {} \; | awk '$$1 > 700 {print}'

be-test:
    poetry run pytest tests/

fe-lint:
    cd frontend && npx eslint src/ --ext .vue,.js

fe-file-len:
    cd frontend && npx eslint src/ --ext .vue,.js

fe-test:
    cd frontend && npx vitest run

test-all: be-test fe-test
