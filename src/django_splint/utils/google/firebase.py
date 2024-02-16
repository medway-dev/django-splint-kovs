from typing import Union

from django.conf import settings
from firebase_admin import auth, db
from firebase_admin.auth import UserRecord
from firebase_admin.db import Reference

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

    @classmethod
    def create(cls, email: str, payload: dict = {}, **kwargs) -> UserRecord:
        """
        Create firebase access for user

        Args:
            email (str): email of user
            payload (dict, optional): payload to create user. Defaults to {}.

        Raises:
            error: EmailAlreadyExistsError

        Returns:
            UserRecord: UserRecord
        """
        LOG.info(
            f"Creating firebase access for user {email}", extra={**kwargs, **payload}
        )
        kwargs.update({"email": email})
        try:
            user = cls.app.create_user(email=clean_email(email), **payload)
        except auth.EmailAlreadyExistsError:
            LOG.warning(
                f"User {email} already exists in firebase", extra={**kwargs, **payload}
            )
            return
        LOG.info(
            f"Created firebase access for user {email}", extra={**kwargs, **payload}
        )
        return user

    @classmethod
    def update_or_create(
        cls, email: str, payload: dict, **kwargs
    ) -> Union[UserRecord, bool]:
        """
        Update or create firebase access for user

        Args:
            email (str): email of user
            payload (dict): payload to update

        Raises:
            error: EmailAlreadyExistsError

        Returns:
            Union[UserRecord, bool]: UserRecord and True if user was created, else False
        """
        LOG.info(
            f"Updating firebase access of user {email}", extra={**kwargs, **payload}
        )
        try:
            user = cls.get(email)
        except auth.UserNotFoundError:
            user = cls.create(cls, **payload)
            LOG.warning(
                f"User {email} not found in firebase, creating new user...",
                extra={**kwargs, **payload},
            )
            return user, True

        try:
            user = cls.app.update_user(user.uid, **payload)
        except auth.EmailAlreadyExistsError:
            LOG.warning(
                f"User {payload['email']} already exists in firebase",
                extra={**kwargs, **payload},
            )
        LOG.info(
            f"Updated firebase access for user {email}", extra={**kwargs, **payload}
        )
        return user, False


class FirebaseDatabase:
    @classmethod
    def reference(
        cls,
        path,
        uid=None,
        url=settings.GOOGLE_FIREBASE_DATABASE_URL,
    ) -> Reference:
        """
        Get firebase database reference

        Args:
            path (str): path to reference
            uid (str, optional): uid of user. Defaults to None.
            url (str, optional): url of firebase database. Defaults to settings.GOOGLE_FIREBASE_DATABASE_URL.

        Returns:
            Reference: firebase database reference
        """
        path = f"/{path}/{uid}/" if uid else f"/{path}/"
        return db.reference(path=path, url=url)

    @classmethod
    def get(
        cls,
        path,
        uid,
        url=settings.GOOGLE_FIREBASE_DATABASE_URL,
    ) -> dict:
        """
        Get firebase database data

        Args:
            path (str): path to reference
            uid (str): uid of user
            url (str, optional): url of firebase database. Defaults to settings.GOOGLE_FIREBASE_DATABASE_URL.

        Returns:
            dict: firebase database data
        """
        return db.reference(path=f"/{path}/{uid}/", url=url).get()
