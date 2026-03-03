"""Application business logic."""
from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_

from app.models import User, ApiKeyApplication, ApiCredential, ApplicationStatus
from app.schemas.application import ApplicationCreate, ApplicationResponse
from app.services.credential import CredentialService
from app.services.apisix import ApisixClient, ApisixError


class ApplicationService:
    """API Key application workflow."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.credential_service = CredentialService(db)
        self.apisix = ApisixClient()

    def create_application(self, data: ApplicationCreate) -> ApiKeyApplication:
        """User submits an application. Create or get user, then application."""
        user = self.db.query(User).filter(User.email == data.email).first()
        if not user:
            user = User(username=data.username, email=data.email)
            self.db.add(user)
            self.db.flush()
        app = ApiKeyApplication(
            user_id=user.id,
            reason=data.reason,
            status=ApplicationStatus.PENDING.value,
        )
        self.db.add(app)
        self.db.commit()
        self.db.refresh(app)
        return app

    def list_applications(
        self,
        status: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> tuple[list[ApiKeyApplication], int]:
        """List applications (admin). Optional status filter."""
        q = self.db.query(ApiKeyApplication).options(
            joinedload(ApiKeyApplication.user),
        )
        if status:
            q = q.filter(ApiKeyApplication.status == status)
        total = q.count()
        items = q.order_by(ApiKeyApplication.created_at.desc()).offset(skip).limit(limit).all()
        return items, total

    def get_application(self, application_id: int) -> Optional[ApiKeyApplication]:
        return (
            self.db.query(ApiKeyApplication)
            .options(joinedload(ApiKeyApplication.user))
            .filter(ApiKeyApplication.id == application_id)
            .first()
        )

    def approve(self, application_id: int) -> ApiCredential:
        """Approve application: create credential and APISIX consumer."""
        app = self.get_application(application_id)
        if not app:
            raise ValueError("Application not found")
        if app.status != ApplicationStatus.PENDING.value:
            raise ValueError(f"Application is not pending: {app.status}")

        credential = self.credential_service.create_for_application(app)
        try:
            self.apisix.create_consumer(
                username=credential.consumer_name,
                api_key_value=credential.api_key,
                quota_per_minute=credential.quota_per_minute,
            )
        except ApisixError as e:
            self.db.rollback()
            raise RuntimeError(f"Failed to create APISIX consumer: {e.message}") from e

        app.status = ApplicationStatus.APPROVED.value
        app.reviewed_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(credential)
        self.db.refresh(app)
        return credential

    def reject(self, application_id: int) -> ApiKeyApplication:
        """Reject application."""
        app = self.get_application(application_id)
        if not app:
            raise ValueError("Application not found")
        if app.status != ApplicationStatus.PENDING.value:
            raise ValueError(f"Application is not pending: {app.status}")
        app.status = ApplicationStatus.REJECTED.value
        app.reviewed_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(app)
        return app

    def delete_application(self, application_id: int) -> None:
        """Delete application. If approved, delete credential and APISIX consumer first."""
        app = self.get_application(application_id)
        if not app:
            raise ValueError("Application not found")
        cred = self.db.query(ApiCredential).filter(ApiCredential.application_id == application_id).first()
        if cred:
            self.credential_service.delete(cred.id)
        # Re-get app after possible commit in credential_service.delete
        app = self.db.query(ApiKeyApplication).filter(ApiKeyApplication.id == application_id).first()
        if app:
            self.db.delete(app)
            self.db.commit()
