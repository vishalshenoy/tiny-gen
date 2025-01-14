# Tinygen Code

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import os
import shutil
import tempfile
from typing import List, Tuple
import git
import openai
from dotenv import load_dotenv
from supabase import create_client, Client

app = FastAPI(
    title="Tinygen",
    description="A very trivial version of Codegen."
)

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_KEY")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
SUPABASE_URL = os.getenv("SUPABASE_URL")

supabase: Client = create_client(
    SUPABASE_URL, SUPABASE_KEY)
client = openai.OpenAI(api_key=OPENAI_API_KEY)

filter_system_prompt = (
    "You are a code assistant tasked with filtering relevant file paths for a given task."
    " You should respond with only the relevant file paths, each on a new line."
)

diff_system_prompt = (
    "You are a helpful assistant for generating code diffs based on file content and user prompts. "
    "Your task is to analyze the provided file content and the user's instructions to determine if any changes "
    "are necessary, and only make functional changes. Also, do not add addition comments to the code. If changes are needed, provide a unified diff that modifies the file to accomplish the task. "
    "If no changes are needed, respond with 'No changes needed.' Only provide the diff or the specified response without any explanations."
)

reflection_system_prompt = (
    "You are a code assistant that reviews diffs for correctness and sufficiency. "
    "Your task is to analyze the provided unified diff and determine if it correctly and sufficiently accomplishes the user's task."
)


class DiffRequest(BaseModel):
    repoUrl: str
    prompt: str


class DiffResponse(BaseModel):
    diff: str


def clone_repo(repo_url: str) -> str:
    temp_dir = tempfile.mkdtemp()
    try:
        print(f"Cloning repository from {repo_url} to {temp_dir}")
        git.Repo.clone_from(repo_url, temp_dir)
    except git.exc.GitError as e:
        shutil.rmtree(temp_dir)
        raise ValueError(f"Failed to clone repository: {e}")
    return temp_dir


def get_repo_files(repo_path: str) -> List[str]:
    repo_files = []
    for root, dirs, files in os.walk(repo_path):
        for file in files:
            file_path = os.path.join(root, file)
            if is_text_file(file_path):
                repo_files.append(file_path)
    print(f"Total text files found: {len(repo_files)}")
    return repo_files


def is_text_file(file_path: str) -> bool:
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            f.read(1024)
        return True
    except:
        return False


def filter_relevant_files_in_batch(repo_files: List[str], prompt: str) -> List[str]:
    file_paths_text = "\n".join(f"- {path}" for path in repo_files)

    user_prompt = f"""
    **File Paths:**
    {file_paths_text}

    **User Prompt:** {prompt}

    **Instructions:**
    - Respond with each relevant file path on a new line.
    - Only include relevant file paths and ensure there is no extraneous text.
    - Format your response as a plain list with no bullet points or additional information.
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": filter_system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.1,
            max_tokens=1500,
        )

        gpt_response = response.choices[0].message.content.strip()

        relevant_files = [
            line.strip() for line in gpt_response.splitlines()
            if line.strip() in repo_files
        ]

        print(f"Relevant files: {relevant_files}")

        return relevant_files
    except Exception as e:
        print(f"Error determining relevance for files: {e}")
        return []


def generate_file_diff(file_path: str, repo_path: str, prompt: str) -> Tuple[str, str]:
    relative_path = os.path.relpath(file_path, repo_path)
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        original_content = f.read()

    user_prompt = f"""
    **File Path:** {relative_path}
    **Current Content:**
    ```{original_content}```

    **User Prompt:** {prompt}

    **Instructions:**
    - If no changes are needed, respond with: "No changes needed."
    - If changes are needed, provide only the unified diff without any explanations.
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": diff_system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.4,
            max_tokens=1500,
        )
        gpt_response = response.choices[0].message.content.strip()
        print(f"Generated diff for {relative_path}: {gpt_response[:60]}...")
        return relative_path, gpt_response
    except Exception as e:
        raise RuntimeError(
            f"OpenAI API error during diff generation for {relative_path}: {e}")


def run_reflection(relative_path: str, diff: str, prompt: str) -> str:
    if diff.lower() == "no changes needed.":
        return ""

    user_prompt = f"""
    **Task:** {prompt}

    **File Path:** {relative_path}

    **Unified Diff:**
    {diff}
    **Instructions:**
    1. Review the diff for correctness and completeness.
    2. If the diff is correct and sufficient, respond with: "The diff is correct."
    3. If corrections or improvements are needed, provide only the improved unified diff without any explanations.
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": reflection_system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.4,
            max_tokens=1500,
        )
        reflection_response = response.choices[0].message.content.strip()
        print(f"Reflection for {relative_path}: {reflection_response[:60]}...")

        if reflection_response.lower() == "the diff is correct.":
            return diff
        elif reflection_response.lower() == "no changes needed.":
            return ""
        else:
            return reflection_response
    except Exception as e:
        raise RuntimeError(
            f"OpenAI API error during reflection for {relative_path}: {e}")


def aggregate_diffs(diffs: List[str]) -> str:
    return "\n".join(diffs)


def process_repository(repo_url: str, prompt: str) -> str:
    repo_path = clone_repo(repo_url)
    try:
        repo_files = get_repo_files(repo_path)
        relevant_files = filter_relevant_files_in_batch(repo_files, prompt)

        all_diffs = []
        for file_path in relevant_files:
            relative_path, initial_diff = generate_file_diff(
                file_path, repo_path, prompt)
            if initial_diff.lower() == "no changes needed.":
                continue

            reflected_diff = run_reflection(
                relative_path, initial_diff, prompt)
            if reflected_diff:
                all_diffs.append(reflected_diff)

        unified_diff = aggregate_diffs(all_diffs)
        return unified_diff

    finally:
        cleanup_repo(repo_path)


def cleanup_repo(repo_path: str):
    try:
        shutil.rmtree(repo_path)
        print(f"Cleaned up repository at {repo_path}")
    except Exception as e:
        print(f"Error cleaning up repository at {repo_path}: {e}")


def store_diff_in_supabase(repo_url: str, prompt: str, diff: str) -> None:
    try:
        supabase.table("diffs").insert({
            "repoUrl": repo_url,
            "prompt": prompt,
            "diff": diff
        }).execute()
        print(
            f"Stored in Supabase: Repo URL: {repo_url}, Prompt: {prompt}, Diff: {diff[:60]}...")
    except Exception as e:
        print(f"Error storing in Supabase: {e}")


@app.post("/generate-diff", response_model=DiffResponse)
def generate_diff_endpoint(request: DiffRequest):
    repo_url = request.repoUrl
    prompt = request.prompt

    try:
        unified_diff = process_repository(repo_url, prompt)

        if not unified_diff:
            response_diff = "No changes were necessary to accomplish the task."
        else:
            response_diff = unified_diff

        store_diff_in_supabase(repo_url, prompt, response_diff)

        return DiffResponse(diff=response_diff)

    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except RuntimeError as re:
        raise HTTPException(status_code=500, detail=str(re))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {e}")
