import urllib
from collections import defaultdict
from typing import List, Dict

import requests
from itertools import islice
from unidiff import PatchSet, PatchedFile, Hunk
from github import Github
import os

from openai_service import OpenAIService

OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')

GITHUB_TOKEN = os.environ.get('GITHUB_TOKEN')
OWNER = os.environ.get('OWNER', "shruti222patel")
REPO_NAME = os.environ.get('REPO_NAME', "repo-gpt")
GIT_HOSTNAME = os.environ.get('GIT_HOSTNAME', "github.com")
BASE_URL = 'https://api.github.com'

IGNORE_FILE_EXTENTIONS = [".ipynb", ".lock"]

# Authenticate with the provided token
g = Github(GITHUB_TOKEN) # Doesn't work: base_url=f"https://{GIT_HOSTNAME}/api/v3"
# Create Openai service
openai_service = OpenAIService(OPENAI_API_KEY)

# Get the repository
repo = g.get_repo(f"{OWNER}/{REPO_NAME}")

def get_all_pr_comments(pull_number):
    # Get the pull request
    pull = repo.get_pull(pull_number)

    # Fetch the comments
    comments = list(pull.get_comments())
    for comment in comments:
        print(comment)
        print(f"commit_id: {comment.commit_id}")

def get_pr_diff_summary(pull_number):

    # Get the pull request
    pull = repo.get_pull(pull_number)
    github_patch_processor = GitDiffProcessor(pull.diff_url)
    head_sha = pull.head.sha
    # Fetch the diff
    files = list(islice(pull.get_files(), 51)) # only pulls the first 50 files updated in the PR
    comments = {}
    for file in files:
        path = file.filename
        patch = file.patch
        contents = repo.get_contents(path, ref=head_sha)
        content = contents.decoded_content.decode()
        if os.path.splitext(path)[1] not in IGNORE_FILE_EXTENTIONS and patch:
            # print("-----------------------------------------------")
            # print(f"Path: {path}")
            # print(f"Patch: {patch}")

            updated_code = github_patch_processor.get_openai_code_output(path)
            # print(updated_code)
            # print("-------")
            comment = openai_service.analyze(updated_code, content)
            # print(comment)

            if "no suggestions" not in comment.lower():
                comments[path] = comment

                # code_suggestions = openai_service.code_suggestions(updated_code, comment)
                # print(code_suggestions)
                # create_review_comment(pull_number, path, code_suggestions)
                # post_github_comment(pull_number, "test", path, 31)
            # get_all_pr_comments(pull_number)
            # post_github_comment(pull_number, "test", path, 31)
            # get_all_pr_comments(pull_number)
            #
            # break

    summary = openai_service.summarize(comments)

    return summary


class GitCodeSuggestion:
    def __init__(self, hunk: Hunk):
        self.hunk = hunk

    def check(self):
        return self.hunk.is_valid()

    def get_git_start_line(self):
        return self.hunk.source_start

    def get_git_end_line(self):
        return self.hunk.source_start + self.hunk.source_length

    def get_git_code(self):
        return "```suggestion\n"+ ''.join(line for line in self.hunk)+"\n```"

class GitDiffProcessor:
    def __init__(self, diff_url: str):
        diff = urllib.request.urlopen(diff_url)
        encoding = diff.headers.get_charsets()[0]
        self.patch = PatchSet(diff, encoding=encoding)
        self.target_code = self.get_target_code_output()

    def get_target_code_output(self) -> Dict[str, List[str]]:
        output = defaultdict(list)
        for patched_file in self.patch:
            for hunk in patched_file:
                if hunk.is_valid():
                    output[patched_file.path].append(hunk.target)
                else:
                    print("Invalid hunk")
                    print(hunk)
        return output


    def get_openai_code_output(self, filename:str) -> List[str]:
        prompt = ""
        for code_snippet in self.target_code[filename]:
            prompt_substring = []
            for line in code_snippet:
                if line.startswith("+"):
                    prompt_substring.append(f" {line[1:]}")
                else:
                    prompt_substring.append(f"{line}")
            prompt += f"```\n...other code\n{''.join(prompt_substring)}...other code\n```\n"
        return prompt





class ProcessOpenAIDiff:
    def __init__(self, openai_response: str):
        self.diff, self.explanation = self.create_unidiff(openai_response)

    def create_unidiff(self, openai_resonse: str) -> (PatchedFile, str):
        """Create a unidiff from the openai response.

        Args:
        - openai_response (str): The openai response.

        Returns:
        - str: The unidiff.
        """

        # Split the response into lines
        lines = openai_resonse.split('\n')

        CODE_DENOTER = '```'
        # Process each line
        inside_code_block = False
        code_diff_lines = []
        text_explanation_lines = []
        for line in lines:
            if line.startswith(CODE_DENOTER):
                inside_code_block = not inside_code_block
                continue
            if inside_code_block:
                code_diff_lines.append(line)
            else:
                text_explanation_lines.append(line)

        patch = PatchSet(code_diff_lines)
        if len(patch) == 0:
            raise ValueError("Expected at least one file in the diff, but got none.")
        elif len(patch) > 1:
            print(
                "Expected only one file in the diff, but got more than 1. Only using the diff from the first file in the patch.")

        return patch[0], '\n'.join(text_explanation_lines)

    def get_git_code_suggestions(self) -> List[GitCodeSuggestion]:
        """Get the git code suggestions from the openai response.

        Returns:
        - List[GitCodeSuggestion]: The git code suggestions.
        """

        return [GitCodeSuggestion(hunk) for hunk in self.diff]






def create_review_comment(pull_number, comment):
    """Creates a review comment on the given pull request.

    Args:
    - pull_number (int): The pull request number.
    - comment (str): The comment to post.
    """

    # Get the pull request
    pull = repo.get_pull(pull_number)

    # pull.create_issue_comment(comment)
    # Post the comment
    commit_id = pull.get_commits().reversed[0]
    print(f"commit_id: {commit_id}")
    print(f"type: {type(commit_id)}")
    pull.create_issue_comment(comment)


def get_latest_commit_sha(pull_number):
    pull = repo.get_pull(pull_number)
    return pull.get_commits().reversed[0].sha

def post_github_comment(pull_number, body, path, start_line, end_line=None):
    print(f"Posting comment on PR #{pull_number} on {path} at line {start_line}")
    print(f"path type: {type(path)}")

    headers = {
        'Authorization': f'token {GITHUB_TOKEN}',
        'Accept': 'application/vnd.github.v3+json',
        'X-GitHub-Api-Version': '2022-11-28'
    }

    end_line = end_line or start_line + 1
    data = {
        'body': body,
        'commit_id': get_latest_commit_sha(pull_number),
        'path': path,
        'start_line': start_line,
        'start_side': 'RIGHT',
        'line': end_line,
        'side': 'RIGHT'
    }

    response = requests.post(f'{BASE_URL}/repos/{OWNER}/{REPO_NAME}/pulls/{pull_number}/comments', headers=headers,
                             json=data)

    if response.status_code == 201:
        print("Comment added successfully!")
    else:
        print(f"Failed to add comment! Status code: {response.status_code}, Response: {response.text}")

    return response

if __name__ == '__main__':
    pull_number = 9
    summary = get_pr_diff_summary(pull_number)

    if "no comments" not in summary.lower():
        print(f"Summary: {summary}")
        # save summary as an issue comment
        create_review_comment(pull_number, summary)