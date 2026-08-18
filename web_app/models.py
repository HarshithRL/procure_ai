from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from .database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_name: Mapped[str | None] = mapped_column(String(120))
    email: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False, index=True
    )
    display_name: Mapped[str | None] = mapped_column(String(120))
    given_name: Mapped[str | None] = mapped_column(String(80))
    family_name: Mapped[str | None] = mapped_column(String(80))
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    groups: Mapped[list | None] = mapped_column(JSON, default=list)
    entitlements: Mapped[list | None] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)

    projects: Mapped[list["Project"]] = relationship(
        back_populates="owner", foreign_keys="Project.owner_email"
    )

    def to_dict(self) -> dict:
        return {
            "id": str(self.id),
            "user_name": self.user_name,
            "email": self.email,
            "display_name": self.display_name,
            "given_name": self.given_name,
            "family_name": self.family_name,
            "active": self.active,
            "groups": self.groups or [],
            "entitlements": self.entitlements or [],
        }


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    category: Mapped[str | None] = mapped_column(String(100))
    region: Mapped[str | None] = mapped_column(String(100))
    vendor_count: Mapped[int] = mapped_column(Integer, default=0)
    doc_count: Mapped[int] = mapped_column(Integer, default=0)
    node_count: Mapped[int] = mapped_column(Integer, default=0)
    edge_count: Mapped[int] = mapped_column(Integer, default=0)
    active_doc_count: Mapped[int] = mapped_column(Integer, default=0)
    target_spend_eur: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    status: Mapped[str] = mapped_column(String(50), default="draft")
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=_utcnow, onupdate=_utcnow
    )
    owner_email: Mapped[str | None] = mapped_column(
        String(255), ForeignKey("users.email"), nullable=True
    )

    owner: Mapped[User | None] = relationship(
        back_populates="projects", foreign_keys=[owner_email]
    )
    documents: Mapped[list["Document"]] = relationship(
        back_populates="project", cascade="all, delete-orphan"
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "category": self.category,
            "region": self.region,
            "vendor_count": self.vendor_count,
            "doc_count": self.doc_count,
            "node_count": self.node_count,
            "edge_count": self.edge_count,
            "active_doc_count": self.active_doc_count,
            "target_spend_eur": float(self.target_spend_eur)
            if self.target_spend_eur
            else 0,
            "status": self.status,
            "updated_at": self.updated_at.isoformat() + "Z"
            if self.updated_at
            else None,
        }


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    project_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("projects.id"), nullable=False
    )
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_type: Mapped[str] = mapped_column(String(10), nullable=False)  # pdf, docx, xlsx
    file_content: Mapped[bytes] = mapped_column(nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="pending")  # pending, processing, complete, error
    error_message: Mapped[str | None] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=_utcnow, onupdate=_utcnow
    )

    project: Mapped[Project] = relationship(
        back_populates="documents", foreign_keys=[project_id]
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "project_id": self.project_id,
            "filename": self.filename,
            "file_type": self.file_type,
            "status": self.status,
            "error_message": self.error_message,
            "created_at": self.created_at.isoformat() + "Z" if self.created_at else None,
            "updated_at": self.updated_at.isoformat() + "Z" if self.updated_at else None,
        }
