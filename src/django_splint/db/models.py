import logging
import uuid
from datetime import datetime

import django.db.models.options as options
from django.contrib.auth.models import UserManager
from django.db import models
from django.db.models.query import QuerySet
from django.forms.models import model_to_dict
from django.utils import timezone

CUSTOM_META_FIELDS = ('original_value_fields',)
options.DEFAULT_NAMES = options.DEFAULT_NAMES + CUSTOM_META_FIELDS

logger = logging.getLogger('activity')


class SplintDeletedManager(models.Manager):
    use_for_related_fields = True

    def get_queryset(self, *args, **kwargs):
        return SplintQuerySet(
            model=self.model, using=self._db, hints=self._hints).filter(
                _deleted=True)


class SplintManager(models.Manager):
    use_for_related_fields = True

    def get_queryset(self, *args, **kwargs):
        return SplintQuerySet(
            model=self.model, using=self._db, hints=self._hints).filter(
                _deleted=False)

    def get_or_none(self, **kwargs):
        try:
            return super(SplintManager, self).get(**kwargs)
        except self.model.DoesNotExist:
            return None


class SplintObjectsWithDeletedManager(models.Manager):
    use_for_related_fields = True

    def get_queryset(self, *args, **kwargs):
        return SplintQuerySet(
            model=self.model, using=self._db, hints=self._hints)


class SplintQuerySet(QuerySet):
    def delete(self):
        """
        Overriding of the delete method.

        This is not the fastest way, altough we garantee that any object will
        not be completely deleted.
        """
        for obj in self:
            obj.delete()

    def force_delete(self):
        """Force delete from DB."""
        return super().delete()


class SplintModel(models.Model):
    ADMIN_ORIGIN = 'admin'
    API_ORIGIN = 'api'

    created_at = models.DateTimeField('Data de criação', auto_now_add=True)
    updated_at = models.DateTimeField('Data de edição', auto_now=True)

    _deleted = models.BooleanField('Deletado', default=False)
    _deleted_at = models.DateTimeField(
        'Data de deleção', null=True, blank=True)

    objects = SplintManager()
    deleted = SplintDeletedManager()
    objects_with_deleted = SplintObjectsWithDeletedManager()

    class Meta:
        abstract = True
        ordering = ['-id']
        original_value_fields = ()
        default_manager_name = 'objects'

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        for field in getattr(self._meta, "original_value_fields", ()):
            setattr(self, f"__original_{field}", self.__dict__.get(field))

    def save(self, log_activity=True, *args, **kwargs):
        """Save overwrite to log every every action in the system."""
        action = self.get_action()

        res = super(SplintModel, self).save(*args, **kwargs)

        if log_activity:
            try:
                # Tenta obter o dicionário do modelo de forma segura
                object_data = self._safe_model_to_dict()
            except Exception as e:
                # Se falhar, usa apenas informações básicas
                logger.warning(
                    f"Erro ao serializar modelo "
                    f"{self.__class__.__name__}: {str(e)}"
                )
                object_data = {
                    'id': getattr(self, 'id', None),
                    'model': self.__class__.__name__,
                    'error': 'Serialization failed'
                }

            log = {
                'action': action,
                'origin': getattr(self, 'origin', None),
                'user': getattr(self, 'user_id', None),
                'model': self.__class__.__name__,
                'object': object_data,
            }

            logger.info(log)

        return res

    def _safe_model_to_dict(self):
        """Safely convert model to dict, handling M2M fields properly."""
        exclude_fields = getattr(self, 'exclude_log', None) or []
        
        # Adiciona campos M2M ao exclude por padrão para evitar problemas
        m2m_fields = [field.name for field in self._meta.many_to_many]
        exclude_fields = list(exclude_fields) + m2m_fields
        
        try:
            return model_to_dict(self, exclude=exclude_fields)
        except Exception:
            # Fallback: retorna apenas campos básicos
            data = {}
            for field in self._meta.fields:
                if field.name not in exclude_fields:
                    try:
                        data[field.name] = getattr(self, field.name)
                    except Exception:
                        data[field.name] = None
            return data

    def delete(self, *args, **kwargs):
        """Delete overwrite to perform soft delete."""
        self._deleted = True
        self._deleted_at = datetime.utcnow().replace(
            tzinfo=timezone.get_current_timezone())
        self.save()

    def force_delete(self, *args, **kwargs):
        """Force delete function."""
        return super(SplintModel, self).delete(*args, **kwargs)

    def get_action(self):
        """Get action for logging."""
        CREATED, UPDATED, DELETED = 'created', 'updated', 'deleted'
        action = None
        if not self.id:
            action = CREATED
        elif self._deleted is True:
            action = DELETED
        else:
            action = UPDATED

        return action


class SplintUserManager(UserManager):

    def _create_user(self, email, password, **extra_fields):
        """Create and save a User with the given email and password."""
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)

        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email=None, password=None, **extra_fields):
        """Create user function."""
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)

        if password is None:
            password = str(uuid.uuid4())[:8]

        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password, **extra_fields):
        """Create super user function."""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self._create_user(email, password, **extra_fields)

    def get_or_none(self, **kwargs):
        """Get user or return None."""
        try:
            return super(SplintUserManager, self).get(**kwargs)
        except self.model.DoesNotExist:
            return None
