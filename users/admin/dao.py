"""DAO for admin."""

from sqlalchemy.orm import Session
from users.admin.dto import AdminDTO
from users.models import Admin


def create_admin(session: Session, dto: AdminDTO):
    """Create a new user in the users table, using the id as primary key."""
    admin = Admin(id=dto.id, email=dto.email, username=dto.username)
    session.add(admin)
    session.commit()
    session.refresh(admin)
    return admin
