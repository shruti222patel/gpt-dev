# Set your OpenAI API key as an environment variable
import os
import time
from typing import Any, Callable, Dict

import openai as openai
from tenacity import (  # for exponential backoff
    retry,
    stop_after_attempt,
    wait_random_exponential,
)

class OpenAIService:
    CODE_REVIEW_SYSTEM_PROMPT_OLD = """You are a helpful and funny world-class software engineer. When provided a git diffs, you analyze it and if there are improvements you can make, you detail the improvements in 3 or less bullets. Your suggestions are actionable, not stylistic. If you cannot make suggestions, you respond with "No suggestions.". The suggestions should not include stylistic improvements like adding typehints or docstrings. Your suggestions are relevant and actionable, considering the provided context."""
    CODE_REVIEW_SYSTEM_PROMPT_OLD = """You are a helpful and funny world-class software engineer. You analyze provided code and you detail the improvements using the following guidelines:
- Provide Constructive Feedback: Be kind and respectful. Frame feedback as suggestions and use questions to provoke thought rather than making authoritative statements. 
- Be concise, constructive, and respectful. Recognize good work. 
- Do not suggest typehint, type hint, docstring, or comment additions.
- Do not make assumptions about the code. Ask questions if anything is unclear.
- Only focus on logical errors, potential bugs, or vulnerabilities introduced by the changes. Consider edge cases and corner scenarios that might not have been accounted for in the initial implementation.
- Avoid Nitpicking. Only focus on significant issues.
- Feedback must be relevant and actionable.
- Output a max of 3 suggestions.
- Review comments should be well organized and easy to read.
If you cannot make suggestions, you respond with "No suggestions."."""

    CODE_REVIEW_SYSTEM_PROMPT = """You are a helpful and funny world-class code reviewer. You provide funny and insightful feedback on the code changes given. You analyze provided code & diffs, and you detail the improvements using the following guidelines:"""

    SUMMARIZE_CODE_REVIEW_SYSTEM_PROMPT = """You are a helpful and funny world-class technical writer. You analyze descriptions of suggested code updates and summarize the most important ones using the following guidelines:
- Provide Constructive Feedback: Be kind and respectful. Frame feedback as suggestions and use questions to provoke thought rather than making authoritative statements. 
- Be concise, constructive, and respectful. Recognize good work. 
- Do not suggest typehint, type hint, docstring, or comment additions.
- Do not make assumptions about the code.  Ask questions if anything is unclear.
- Only focus on logical errors, potential bugs, or vulnerabilities introduced by the changes. Consider edge cases and corner scenarios that might not have been accounted for in the initial implementation.
- Avoid Nitpicking. Only focus on significant issues.
- Feedback must be relevant and actionable.
- Output a max of 3 suggestions.
- Review comments should be well organized and easy to read.
Structure and organize your response using markdown and emojis. If there is nothing to summarize, you respond with "No suggestions."."""

    CODE_SUGGESTION_SYSTEM_PROMPT = """You are a world-class software engineer. When provided a code snippet, you analyze it and if there are improvements you can make, you respond with the improved code diff. If there aren't impromvents you can make, you respond with "No suggestions." ONLY."""

    PR_REVIEW_COMMENT_SYSTEM_PROMPT = """You are a helpful and funny world-class software engineer. Given a list of code suggestions, you respond with a summary of the suggestions. You format your suggestions in easy to read markdown. If there are no comments, write "No comments.". Your summary is relevant and actionable, considering the provided context. You use emojis where appropriate."""

    def __init__(self, openai_api_key: str):
        openai.api_key = openai_api_key
        self.GPT_MODEL = "gpt-3.5-turbo"

    @retry(wait=wait_random_exponential(min=0.2, max=60), stop=stop_after_attempt(6))
    def analyze(
        self, diff: str, content: str
    ):
        query = f"""Your task is:
- Review the code changes and provide feedback.
- Highlight bugs them.
- Provide details on missed use of best-practices.
- Do not highlight minor issues and nitpicks.
- Use bullet points if you have multiple comments.
- Provide security recommendations if there are any.
- If there are no suggestions, write "No suggestions."
Full file:
{content}
Diff to review:
{diff}"""

        response = openai.ChatCompletion.create(
            messages=[
                {
                    "role": "system",
                    "content": self.CODE_REVIEW_SYSTEM_PROMPT,
                },
                {"role": "user", "content": query},
            ],
            model=self.GPT_MODEL,
            temperature=0,
        )
        return response.choices[0]["message"]["content"]
    @retry(wait=wait_random_exponential(min=0.2, max=60), stop=stop_after_attempt(6))
    def code_suggestions(
        self, diff: str, text_suggestions: str
    ):
        query = f"""Based on the code recommendations listed, output code suggestions in the unified format diff.
Code recommendations:
{text_suggestions}
Code to review:
{diff}"""

        print(query)

        response = openai.ChatCompletion.create(
            messages=[
                {
                    "role": "system",
                    "content": self.CODE_SUGGESTION_SYSTEM_PROMPT,
                },
                {"role": "user", "content": query},
            ],
            model=self.GPT_MODEL,
            temperature=1,
        )
        return response.choices[0]["message"]["content"]


    @retry(wait=wait_random_exponential(min=0.2, max=60), stop=stop_after_attempt(6))
    def summarize(
        self, comments: Dict[str, str]
    ):
        query = "\n".join([f"\nFile: {k}\n{v}" for k, v in comments.items()])
        print(query)

        response = openai.ChatCompletion.create(
            messages=[
                {
                    "role": "system",
                    "content": self.SUMMARIZE_CODE_REVIEW_SYSTEM_PROMPT,
                },
                {"role": "user", "content": query},
            ],
            model=self.GPT_MODEL,
            temperature=0,
        )
        return response.choices[0]["message"]["content"]