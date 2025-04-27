import uuid
from typing import Optional

from sqlalchemy import UUID, DateTime, func
from sqlalchemy.ext.declarative import as_declarative, declarative_base
from sqlalchemy.orm import Mapped, mapped_column

Base = declarative_base()


@as_declarative()
class Base:
    '''
    =====================================================
    # Base model to include default columns for all tables.
    =====================================================
    '''
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    deleted_at: Mapped[Optional[DateTime]] = mapped_column(DateTime(timezone=True), nullable=True)

    created_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), nullable=True)  # Track the creator
    updated_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), nullable=True)  # Track the updater
    deleted_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), nullable=True)  # Soft delete column

