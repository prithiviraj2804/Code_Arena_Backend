from fastapi import APIRouter


router = APIRouter()


@router.get("/")
async def root():
    """
    Root endpoint that returns a simple message.
    """
    return {"message": "Welcome to the Code_Arena API!"}