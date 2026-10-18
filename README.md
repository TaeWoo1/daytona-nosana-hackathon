# daytona-nosana-hackathon

Hackathon project using [Daytona](https://www.daytona.io/) sandboxes and [Nosana](https://nosana.com/) GPU compute.

## Setup

```bash
# Python (Daytona SDK)
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Node (Nosana CLI / SDK)
npm install

# API keys
cp .env.example .env   # then fill in the keys
```

## Smoke test

```bash
python smoke_test.py   # creates a Daytona sandbox, runs code, deletes it
npx nosana --help
```
