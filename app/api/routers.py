from fastapi import APIRouter, Depends

from app.utils.security import decode_token


router = APIRouter()


@router.get("/")
async def root(token = Depends(decode_token)):
    """
    Root endpoint that returns a simple message.
    """
    id = token.get("id")
    if id:
        return {"message": "Welcome to the Code_Arena API!", "id": id}
    else:
        return {"message": "Welcome to the Code_Arena API!"}
