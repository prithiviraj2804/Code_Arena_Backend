import json
from math import e
from app.api.schemas import UserProgram
from fastapi import APIRouter, Depends

from app.utils.security import decode_token, get_current_user
import httpx
from app.core.config import settings


router = APIRouter()


@router.get("/")
async def check(token = Depends(get_current_user)):
    """
    Root endpoint that returns a simple message.
    """
    return {"message": f"Hello, f{token}!"}


@router.get("/problems")
async def get_problems():
    """
    Endpoint to get problems.
    """
    try:
        with open("problems.json") as f:
            problems = json.load(f)
        return problems

    except Exception as e:
        raise e

@router.get("/problems/{problem_id}")
async def get_problem(problem_id: int):
    """
    Endpoint to get a specific problem by ID.
    """
    try:
        with open("problems.json") as f:
            problems = json.load(f)
        problem = next((p for p in problems if p["id"] == problem_id), None)
        if not problem:
            return {"error": "Problem not found"}
        return problem

    except Exception as e:
        raise e

@router.post("/submit")
async def submit_code(code: UserProgram):
    """
    Endpoint to submit code for execution.
    """
    try:
        data = {
            "source_code": code.source_code,
            "language_id": code.language_id,
            "command_line_arguments": code.command_line_arguments,
        }

        print(data)

        JUDGE0_API_URL = f"{settings.code_arena_api_url}/submissions?base64_encoded=false&wait=true"
        HEADERS = {
            "Content-Type": "application/json",
            # Add your RapidAPI key if required:
            # "X-RapidAPI-Key": "<YOUR_RAPIDAPI_KEY>",
            # "X-RapidAPI-Host": "judge0-ce.p.rapidapi.com"
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(JUDGE0_API_URL, headers=HEADERS, json=data)
            response.raise_for_status()
            print(response.json())
            result = response.json()
        return result
    except Exception as e:
        raise e

@router.get("/submissions")
async def get_submissions():
    """
    Endpoint to get all submissions.
    """
    try:
        JUDGE0_API_URL = f"{settings.code_arena_api_url}/submissions?base64_encoded=false"
        HEADERS = {
            "Content-Type": "application/json",
            # Add your RapidAPI key if required:
            # "X-RapidAPI-Key": "<YOUR_RAPIDAPI_KEY>",
            # "X-RapidAPI-Host": "judge0-ce.p.rapidapi.com"
        }

        async with httpx.AsyncClient() as client:
            response = await client.get(JUDGE0_API_URL, headers=HEADERS)
            response.raise_for_status()
            print(response.json())
            result = response.json()
        return result
    except Exception as e:
        raise e

@router.get("/submit/{submission_id}")
async def get_submission(submission_id: str):
    """
    Endpoint to get the result of a submission by ID.
    """
    try:
        JUDGE0_API_URL = f"{settings.code_arena_api_url}/submissions/{submission_id}?base64_encoded=false"
        HEADERS = {
            "Content-Type": "application/json",
            # Add your RapidAPI key if required:
            # "X-RapidAPI-Key": "<YOUR_RAPIDAPI_KEY>",
            # "X-RapidAPI-Host": "judge0-ce.p.rapidapi.com"
        }

        async with httpx.AsyncClient() as client:
            response = await client.get(JUDGE0_API_URL, headers=HEADERS)
            response.raise_for_status()
            print(response.json())
            result = response.json()
        return result
    except Exception as e:
        raise e

@router.get("/system_info")
async def get_system_info():
    """
    Endpoint to get system information.
    """
    try:
        JUDGE0_API_URL = f"{settings.code_arena_api_url}/system_info"
        HEADERS = {
            "Content-Type": "application/json",
            # Add your RapidAPI key if required:
            # "X-RapidAPI-Key": "<YOUR_RAPIDAPI_KEY>",
            # "X-RapidAPI-Host": "judge0-ce.p.rapidapi.com"
        }

        async with httpx.AsyncClient() as client:
            response = await client.get(JUDGE0_API_URL, headers=HEADERS)
            response.raise_for_status()
            print(response.json())
            result = response.json()
        return result
    except Exception as e:
        raise e

@router.get("/statistics")
async def get_statistics():
    """
    Endpoint to get statistics.
    """
    try:
        JUDGE0_API_URL = f"{settings.code_arena_api_url}/statistics"
        HEADERS = {
            "Content-Type": "application/json",
            # Add your RapidAPI key if required:
            # "X-RapidAPI-Key": "<YOUR_RAPIDAPI_KEY>",
            # "X-RapidAPI-Host": "judge0-ce.p.rapidapi.com"
        }

        async with httpx.AsyncClient() as client:
            response = await client.get(JUDGE0_API_URL, headers=HEADERS)
            response.raise_for_status()
            print(response.json())
            result = response.json()
        return result
    except Exception as e:
        raise e

@router.get("/languages")
async def get_languages():
    """
    Endpoint to get all programming languages.
    """
    try:
        JUDGE0_API_URL = f"{settings.code_arena_api_url}/languages"
        HEADERS = {
            "Content-Type": "application/json",
            # Add your RapidAPI key if required:
            # "X-RapidAPI-Key": "<YOUR_RAPIDAPI_KEY>",
            # "X-RapidAPI-Host": "judge0-ce.p.rapidapi.com"
        }

        async with httpx.AsyncClient() as client:
            response = await client.get(JUDGE0_API_URL, headers=HEADERS)
            response.raise_for_status()
            print(response.json())
            result = response.json()
        return result
    except Exception as e:
        raise e
