# Set your OpenAI API key as an environment variable
import os
import time
from typing import Any, Callable

import openai as openai
from tenacity import (  # for exponential backoff
    retry,
    stop_after_attempt,
    wait_random_exponential,
)





class OpenAIService:
    CODE_REVIEW_SYSTEM_PROMPT = """You are a world-class software engineer. When provided a code snippet, you analyze it and offer any code suggestions to improve it. If you have suggestions, you present them in the following GitHub suggestion format:
```suggestion
-[Code you want to remove]
+[Your code suggestion here]
```
If no improvements or suggestions are identified,  write "No suggestions.". Your suggestions are relevant and actionable, considering the provided context."""

    PR_REVIEW_COMMENT_SYSTEM_PROMPT = """You are a world-class software engineer and writer. Given a list of PR review comments, you provide a summary of the comments. If there are no comments, write "No comments.". Your summary is relevant and actionable, considering the provided context."""

    def __init__(self, openai_api_key: str):
        openai.api_key = openai_api_key
        self.GPT_MODEL = "gpt-3.5-turbo"

    @retry(wait=wait_random_exponential(min=0.2, max=60), stop=stop_after_attempt(6))
    def analyze(
        self, diff: str, system_prompt: str = CODE_REVIEW_SYSTEM_PROMPT
    ):
        query = f"""Review the code below and provide code suggestions.  If there are no improvements or suggestions, write "No suggestions.".
        ```
        {diff}
        ```
        """

        response = openai.ChatCompletion.create(
            messages=[
                {
                    "role": "system",
                    "content": system_prompt,
                },
                {"role": "user", "content": query},
            ],
            model=self.GPT_MODEL,
            temperature=0,
        )
        return response.choices[0]["message"]["content"]


    @retry(wait=wait_random_exponential(min=0.2, max=60), stop=stop_after_attempt(6))
    def summarize(
        self, comments: [str], system_prompt: str = CODE_REVIEW_SYSTEM_PROMPT
    ):

        query = "\n* ".join(comments)

        response = openai.ChatCompletion.create(
            messages=[
                {
                    "role": "system",
                    "content": system_prompt,
                },
                {"role": "user", "content": query},
            ],
            model=self.GPT_MODEL,
            temperature=0,
        )
        return response.choices[0]["message"]["content"]