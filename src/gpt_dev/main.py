from itertools import islice

from github import Github
import os

from openai_service import OpenAIService

OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')

GITHUB_TOKEN = os.environ.get('GITHUB_TOKEN', "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")
OWNER = os.environ.get('OWNER', "shruti222patel")
REPO_NAME = os.environ.get('REPO_NAME', "repo-gpt")
BASE_URL = os.environ.get('BASE_URL', "https://github.com")

IGNORE_FILE_EXTENTIONS = [".ipynb", ".lock"]

# Authenticate with the provided token
g = Github(GITHUB_TOKEN)
# Create Openai service
openai_service = OpenAIService(OPENAI_API_KEY)

# Get the repository
repo = g.get_repo(f"{OWNER}/{REPO_NAME}")


def extract_final_code_from_patch(patch):
    """Extracts final code from a git patch by removing lines starting with '-'
    and stripping leading '+' from added lines.

    Args:
    - patch (str): The git diff patch text.

    Returns:
    - str: The final code after applying changes from the patch.
    """

    # Split the patch into lines
    lines = patch.split('\n')

    # Process each line
    processed_lines = []
    for line in lines:
        if line.startswith('-'):
            # Ignore removed lines
            continue
        # Strip the leading '+' and ' ', then add to the result
        processed_lines.append(line[1:])

    return '\n'.join(processed_lines)

def get_pr_diff(pull_number):

    # Get the pull request
    pull = repo.get_pull(pull_number)

    # Fetch the diff
    files = list(islice(pull.get_files(), 51))
    comments = {}
    for file in files:
        path = file.filename
        patch = file.patch
        # contents = repo.get_contents(path, ref=head_sha)
        # content = contents.decoded_content.decode()
        if os.path.splitext(path)[1] not in IGNORE_FILE_EXTENTIONS and patch:
            print("-----------------------------------------------")
            updated_code = extract_final_code_from_patch(patch)
            print(updated_code)
            print("-------")
            comment = openai_service.analyze(path, updated_code)
            print(comment)
            comments[path] = comment

    summary = openai_service.summarize(comments.values())

    return summary


diff = get_pr_diff(9)
print(diff)
