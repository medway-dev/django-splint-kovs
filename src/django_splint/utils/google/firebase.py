from django.conf import settings
from firebase_admin import auth, db

from ..api.authentication import clean_email
from ..aws.function.logging import Logger

LOG = Logger(__name__)


class FirebaseAuth:
    # _base_path = "https://identitytoolkit.googleapis.com/v1"
    # _api_key = settings.GOOGLE_APPLICATION_KEY
    # _url = "accounts"
    app = auth

    @classmethod
    def get(cls, email, uid=None):
        if uid:
            return cls.app.get_user(uid)
        return cls.app.get_user_by_email(email)

    def create(self, email: str, payload: dict = {}, **kwargs) -> None:
        LOG.info(
            f"Creating firebase access for user {email}", extra={**kwargs, **payload}
        )
        kwargs.update({"email": email})
        try:
            self.app.create_user(email=clean_email(email), **payload)
        except auth.EmailAlreadyExistsError:
            LOG.warning(
                f"User {email} already exists in firebase", extra={**kwargs, **payload}
            )
            return
        LOG.info(
            f"Created firebase access for user {email}", extra={**kwargs, **payload}
        )

    def update_or_create(self, email: str, payload: dict, **kwargs) -> None:
        LOG.info(
            f"Updating firebase access of user {email}", extra={**kwargs, **payload}
        )
        try:
            user = self.get(email)
        except auth.UserNotFoundError:
            self.create(**payload)
            LOG.warning(
                f"User {email} not found in firebase, creating new user...",
                extra={**kwargs, **payload},
            )
            return

        try:
            user = self.app.update_user(user.uid, **payload)
        except auth.EmailAlreadyExistsError:
            LOG.warning(
                f"User {payload['email']} already exists in firebase",
                extra={**kwargs, **payload},
            )
            return
        LOG.info(
            f"Updated firebase access for user {email}", extra={**kwargs, **payload}
        )


class FirebaseDatabase:

    @classmethod
    def get(self, path, uid):
        return (
            db
            .reference(
                path=f"/{path}/{uid}/",
                url=settings.GOOGLE_FIREBASE_DATABASE_URL)
            .get()
        )
