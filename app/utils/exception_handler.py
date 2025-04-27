import asyncio
import re
from json import JSONDecodeError

from fastapi import HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from jose import ExpiredSignatureError, JWTError
from sqlalchemy.exc import (DataError, IntegrityError, InterfaceError,
                            OperationalError, ProgrammingError,
                            SQLAlchemyError)

from logs.logging import logger
from main import app
from app.core.config import settings


def json_response_with_cors(content, status_code):
    return JSONResponse(
        content=content,
        status_code=status_code,
        headers={
            "Access-Control-Allow-Origin": "*",  # Modify this for security in production
            "Access-Control-Allow-Credentials": "true"
        }
    )


'''
=====================================================
# Request Validation Exception Handler
=====================================================
'''


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.warning(
        f"Validation error: {exc.errors()} on request {request.url}")
    return json_response_with_cors(
        status_code=422,
        content={"detail": "Invalid request format", "errors": exc.errors()}
    )

'''
=====================================================
# HTTP Exception Handler
=====================================================
'''


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    logger.error(
        f"HTTP Exception {exc.status_code}: {exc.detail} - {request.url}")
    return json_response_with_cors(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )

'''
=====================================================
# Database Exception Handlers
=====================================================
'''


@app.exception_handler(SQLAlchemyError)
async def database_exception_handler(request: Request, exc: SQLAlchemyError):
    logger.error(f"Database error on request {request.url}: {exc}")

    # Rollback the session
    try:
        from app.core.db import get_write_session  # Import your session management function
        session = get_write_session()
        session.rollback()
    except Exception as rollback_exc:
        logger.error(f"Error during session rollback: {rollback_exc}")

    return json_response_with_cors(
        status_code=500,
        content={"detail": "A database error occurred. Please try again later."}
    )

'''
=====================================================
# Integrity Error Handler
=====================================================
'''


@app.exception_handler(IntegrityError)
async def integrity_error_handler(request: Request, exc: IntegrityError):
    logger.warning(f"Database Integrity Error on {request.url}: {exc}")

    # Default fallback message
    error_message = "A record with that value already exists."

    # 1) Try to pull column/value from psycopg2 diagnostics (PostgreSQL)
    orig = exc.orig
    diag = getattr(orig, 'diag', None)
    if diag is not None and diag.column_name:
        col = diag.column_name
        # psycopg2 doesn't expose column_value by default; parse DETAIL if present
        detail = getattr(orig, 'pgerror', '') or str(orig)
        # Try to extract the exact value from the DETAIL clause
        m = re.search(rf'\({col}\)=\((?P<val>[^\)]+)\)', detail)
        val = m.group('val') if m else None

        if val:
            error_message = f"{col} '{val}' already exists."
        else:
            error_message = f"Duplicate value for '{col}'."

    else:
        # 2) Fallback regex on generic exception text
        m = re.search(
            r'Key \((?P<field>[^)]+)\)=\((?P<value>[^)]+)\)', str(orig))
        if m:
            field = m.group('field')
            value = m.group('value')
            error_message = f"{field} '{value}' already exists."

    return json_response_with_cors(
        status_code=409,
        content={"detail": error_message}
    )

'''
=====================================================
# Data Error Handler
=====================================================
'''


@app.exception_handler(DataError)
async def data_error_handler(request: Request, exc: DataError):
    logger.warning(f"Database Data Error on {request.url}: {exc}")

    orig = exc.orig
    diag = getattr(orig, "diag", None)

    if diag and diag.column_name:
        # Column that caused the error
        col = diag.column_name

        # Try to get a user‐friendly message
        msg = getattr(diag, "message_primary", None) or getattr(
            diag, "message_detail", None)
        if msg:
            error_message = f"Invalid data for '{col}': {msg}"
        else:
            error_message = f"Invalid data for column '{col}'."
    else:
        # Fallback: use the first line of the raw error
        raw = str(orig).splitlines()[0]
        error_message = raw or "Invalid data format."

    return json_response_with_cors(
        status_code=422,
        content={"detail": error_message}
    )

'''
=====================================================
# Operational Error Handler
=====================================================
'''


@app.exception_handler(OperationalError)
async def operational_error_handler(request: Request, exc: OperationalError):
    # Log full traceback for diagnostics
    logger.error(
        f"Operational Database Error on {request.url}: {exc}", exc_info=True)

    orig = exc.orig
    diag = getattr(orig, "diag", None)

    if diag:
        # Prefer a primary or detail message if Postgres provides one
        msg = diag.message_primary or diag.message_detail or str(orig)
    else:
        # Fallback to the first line of the raw error text
        msg = str(orig).splitlines()[0]

    # 503 Service Unavailable is more semantically correct for connectivity failures
    return json_response_with_cors(
        status_code=503,
        content={"detail": f"Database connection error: {msg}"}
    )

'''
=====================================================
# Programming Error Handler
=====================================================
'''


@app.exception_handler(ProgrammingError)
async def programming_error_handler(request: Request, exc: ProgrammingError):
    # 1) Log full traceback so you can see exactly where & why
    logger.error(
        f"Database Programming Error on {request.url}: {exc}", exc_info=True)

    orig = exc.orig
    diag = getattr(orig, "diag", None)

    # 2) Try to get a primary/detail message from Postgres if available
    if diag:
        msg = diag.message_primary or diag.message_detail or ""
        # strip any internal hints
        detail = msg.splitlines()[0] if msg else ""
    else:
        detail = ""

    # 3) Fallback to the raw error’s first line
    if not detail:
        detail = str(orig).splitlines()[0]

    return json_response_with_cors(
        status_code=500,
        content={"detail": f"Database query error: {detail}"}
    )

'''
=====================================================
# Interface Error Handler
=====================================================
'''


@app.exception_handler(InterfaceError)
async def interface_error_handler(request: Request, exc: InterfaceError):
    # 1) Log full traceback
    logger.error(
        f"Database Interface Error on {request.url}: {exc}", exc_info=True)

    # 2) Try to pull a clean message from Postgres diagnostics
    orig = getattr(exc, "orig", exc)
    diag = getattr(orig, "diag", None)

    if diag:
        msg = diag.message_primary or diag.message_detail or str(orig)
    else:
        # 3) Fallback to the first line of the raw error text
        msg = str(orig).splitlines()[0]

    # 4) 503 is more semantically correct for connectivity/interface failures
    return json_response_with_cors(
        status_code=503,
        content={"detail": f"Database interface error: {msg}"}
    )

'''
=====================================================
# Timeout Error Handler
=====================================================
'''


@app.exception_handler(asyncio.TimeoutError)
async def timeout_error_handler(request: Request, exc: asyncio.TimeoutError):
    # Log full traceback so you can see exactly where the timeout occurred
    logger.error(f"Timeout Error on {request.url}: {exc}", exc_info=True)

    # Return a clear 504 Gateway Timeout
    return json_response_with_cors(
        status_code=504,
        content={"detail": "Request processing timed out. Please try again later."}
    )

'''
=====================================================
# Permission Error Handler
=====================================================
'''


@app.exception_handler(PermissionError)
async def permission_error_handler(request: Request, exc: PermissionError):
    # 1) Log full context and traceback for debugging
    logger.warning(f"Permission Denied on {request.url}: {exc}", exc_info=True)

    # 2) Use the exception’s message if provided, otherwise fall back to a default
    detail_msg = str(
        exc) or "You do not have permission to perform this action."

    return json_response_with_cors(
        status_code=403,
        content={"detail": detail_msg}
    )

'''
=====================================================
# Authentication Error Handler
=====================================================
'''


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    # 1) Log differently for auth vs. other HTTP errors
    if exc.status_code == 401:
        logger.warning(
            f"Authentication failed: {request.method} {request.url} → {exc.detail}",
            exc_info=True
        )
    else:
        logger.error(
            f"HTTP {exc.status_code} error: {request.method} {request.url} → {exc.detail}",
            exc_info=True
        )

    # 2) Always return the same CORS-wrapped JSON structure
    return json_response_with_cors(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )

'''
=====================================================
# Value Error Handler
=====================================================
'''


@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    # 1) Log with traceback so you can pinpoint where it came from
    logger.warning(
        f"ValueError in {request.method} {request.url} → {exc}",
        exc_info=True
    )

    # 2) Use the exception’s message if it’s meaningful, else fall back
    detail_msg = str(exc).strip() or "Invalid value provided."

    return json_response_with_cors(
        status_code=400,
        content={"detail": detail_msg}
    )

'''
=====================================================
# Type Error Handler
=====================================================
'''


@app.exception_handler(TypeError)
async def type_error_handler(request: Request, exc: TypeError):
    # 1) Log full context and stack trace for easier debugging
    logger.warning(
        f"TypeError in {request.method} {request.url}: {exc}",
        exc_info=True
    )

    # 2) Use the exception’s message if available, otherwise fall back
    detail_msg = str(exc).strip(
    ) or "Invalid data type provided. Please check your input format."

    return json_response_with_cors(
        status_code=400,
        content={"detail": detail_msg}
    )

'''
=====================================================
# Global Exception Handler
=====================================================
'''


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    # Log full stack trace with method & URL context
    logger.exception(
        f"Unhandled exception in {request.method} {request.url}: {exc}")

    return json_response_with_cors(
        status_code=500,
        content={"detail": "An unexpected error occurred. Please contact support."}
    )

'''
=====================================================
# JWT Error Handler
=====================================================
'''


@app.exception_handler(JWTError)
async def jwt_error_handler(request: Request, exc: JWTError):
    # Log with full context and stack trace
    logger.warning(
        f"JWT error in {request.method} {request.url}: {exc}",
        exc_info=True
    )

    # Distinguish expired tokens from other JWT errors
    if isinstance(exc, ExpiredSignatureError):
        detail_msg = "Authentication token has expired. Please log in again."
    else:
        detail_msg = "Invalid authentication token. Please provide a valid token."

    return json_response_with_cors(
        status_code=401,
        content={"detail": detail_msg}
    )

'''
=====================================================
# JSON Decode Error Handler
=====================================================
'''


@app.exception_handler(JSONDecodeError)
async def json_decode_error_handler(request: Request, exc: JSONDecodeError):
    # 1) Log with full context and traceback
    logger.warning(
        f"JSONDecodeError in {request.method} {request.url} at "
        f"line {exc.lineno}, column {exc.colno}: {exc.msg}",
        exc_info=True
    )

    # 2) Build a precise client‐facing message
    detail_msg = (
        f"Invalid JSON at line {exc.lineno}, column {exc.colno}: {exc.msg}"
    )

    return json_response_with_cors(
        status_code=400,
        content={"detail": detail_msg}
    )


