from django.db import models
from django.db.models import signals
from django.dispatch import receiver
from django.forms import ModelForm
from django.core import validators
from django.utils import timezone
from django.utils.http import urlquote
from django.utils.translation import ugettext_lazy as _
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.contrib.auth.models import UserManager

from django_adelaidex.fields import NullableCharField
from django_adelaidex.widgets import SelectTimeZoneWidget


class UserManager(UserManager):

    def create_superuser(self, username, email=None, password=None, **extra_fields):
        return self._create_user(username, email, password, is_staff=False, is_superuser=True,
                                 **extra_fields)

    def create_staffuser(self, username, email=None, password=None, **extra_fields):
        return self._create_user(username, email, password, is_staff=True, is_superuser=False,
                                 **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """
    Duplicate of the django AbstractUser model, customised for edX LTI users.

    Username, password and email are required. Other fields are optional.
    """
    username = models.CharField(_('username'), max_length=255, unique=True,
        help_text=_('Required. 255 characters or fewer. Letters, digits and '
                    '@.+:_- only.'),
        validators=[
            validators.RegexValidator(r'^[\w.@+:-]+$', _('Enter a valid username.'), 'invalid'),
        ])
    first_name = NullableCharField(_('nickname'), max_length=255, unique=True,
            blank=True, null=True, default=None,
            help_text=_('255 characters or fewer. Letters, digits and '
                        '@/./+/-/_ only.'),
            validators=[
                validators.RegexValidator(r'^[\w.@+-]+$', _('Please enter a valid nickname.'), 'invalid'),
            ])
    last_name = models.CharField(_('last name'), max_length=255, blank=True)
    email = models.EmailField(_('email address'), blank=True)
    is_staff = models.BooleanField(_('staff status'), default=False,
        help_text=_('Designates whether the user can log into this admin '
                    'site and have Staff Member group permissions.'))
    is_active = models.BooleanField(_('active'), default=True,
        help_text=_('Designates whether this user should be treated as '
                    'active. Unselect this instead of deleting accounts.'))
    date_joined = models.DateTimeField(_('date joined'), default=timezone.now)

    time_zone = models.CharField(_('timezone'), max_length=255,
        blank=True, null=True, default=None,
        help_text=_('Timezone to use when displaying dates and times.'))

    objects = UserManager()

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['first_name']

    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')
        db_table = 'auth_user'

    def __unicode__(self):
        return self.get_short_name() or self.username

    def __str__(self):
        return unicode(self).encode('utf-8')

    def get_full_name(self):
        """
        Returns the first_name plus the last_name, with a space in between.
        """
        full_name = '%s %s' % (self.first_name, self.last_name)
        return full_name.strip()

    def get_short_name(self):
        "Returns the short name for the user."
        return self.first_name

    def email_user(self, subject, message, from_email=None, **kwargs):
        """
        Sends an email to this User.
        """
        send_mail(subject, message, from_email, [self.email], **kwargs)


@receiver(signals.post_save, sender=User)
def post_save(sender, instance=None, **kwargs):
    '''user.is_staff determines membership in STAFF_MEMBER_GROUP'''
    staff_group = getattr(settings, 'ADELAIDEX_LTI', {}).get('STAFF_MEMBER_GROUP')
    if staff_group:
        if instance.is_staff:
            instance.groups.add(staff_group)
        else:
            instance.groups.remove(staff_group)


class UserForm(ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'time_zone',]
        widgets = {
            'time_zone': SelectTimeZoneWidget,
        }

    def __init__(self, *args, **kwargs):
        super(UserForm, self).__init__(*args, **kwargs)

        # n.b I have no idea why ModelForm doesn't already do this!
        for field in self._meta.fields:
            self.fields[field].validators = self._meta.model._meta.get_field(field).validators

        # Require the user to provide a nickname
        first_name = self.fields['first_name']
        first_name.required = True

    def clean_first_name(self):
        # Strip leading/trailing spaces from nickname
        first_name = self.cleaned_data.get('first_name', '').strip()
        return first_name
