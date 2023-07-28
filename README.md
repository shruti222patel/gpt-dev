# GPT-DEV (WIP)
This tool uses GPT to review PRs and leaves actionable PR comments.

## Installation
Git clone the repo and install the dependencies with poetry:
```bash
poetry install
```

## Usage
Add the following to your `.env` file:
- `OPENAI_API_KEY`
- `GITHUB_TOKEN` 
```bash
poetry shell
source .env
python gpt_dev/main.py
```

Note: right now the repo name, pr number, etc are hardcoded in `main.py`. For now, you'll need to update them in that script.