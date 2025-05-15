from fastapi import APIRouter, Depends

from app.utils.security import decode_token, get_current_user


router = APIRouter()


@router.get("/")
async def check(token :dict = Depends(get_current_user)):
    """
    Root endpoint that returns a simple message.
    """
    return {"message": f"Hello, f{token['id']}!"}