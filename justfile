default:
  @just --list

dev:
  cd frontend && npm run dev

test:
  cd frontend && npm run test

lint:
  cd frontend && npm run lint

build:
  cd frontend && npm run build

preview:
  cd frontend && npm run preview
