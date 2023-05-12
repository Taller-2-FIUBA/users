"""DAO for admin."""

from sqlalchemy.orm import Session
from users.admin.dto import AdminCreationDTO
from users.models import Admin as AdminTable


def create_admin(session: Session, dto: AdminCreationDTO):
    """Create a new user in the users table, using the id as primary key."""
    admin = AdminTable(email=dto.email, username=dto.username)
    session.add(admin)
    session.commit()
    session.refresh(admin)
    return admin


def get_admin_by_email(session: Session, email: str):
    """Return all admins in the database."""
    return session.query(AdminTable).filter(AdminTable.email == email).first()


def get_all(session: Session):
    """Return all admins in the database."""
    return session.query(AdminTable).all()
