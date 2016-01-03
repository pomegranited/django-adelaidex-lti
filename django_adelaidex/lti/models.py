from django.db import models, transaction, IntegrityError
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
from django.core.exceptions import ValidationError
import re

from django_adelaidex.util.fields import NullableCharField, UniqueBooleanField
from django_adelaidex.util.widgets import SelectTimeZoneWidget


class Cohort(models.Model):
    class Meta:
        db_table = 'auth_cohort'

    title = models.CharField(_('title'), max_length=500,
        help_text=_('Required. Will be displayed to students as the "course name" on the login screen.'),
    )

    login_url = models.URLField(_('login url'), max_length=500,
        help_text=_('Required. Choose a URL in your course that displays the LTI component.'),
    )
    enrol_url = models.URLField(_('enrol url'), max_length=500, blank=True, null=True, default=None,
        help_text=_('Optional. Provide a URL for students to enrol in your course.'),
    )
    oauth_key = models.CharField(_('oauth key'), max_length=255, unique=True,
        help_text=_('Required. 255 characters or fewer, but must be unique. Letters, digits and '
                    '.+:_- only.'),
        validators=[
            validators.RegexValidator(r'^[\w.@+:-]+$', _('Enter a valid oauth key.'), 'invalid'),
        ])
    oauth_secret = models.CharField(_('oauth secret'), max_length=255, unique=True,
        help_text=_('Required. 255 characters or fewer. Letters, digits, spaces and '
                    '.+:_- only.'),
        validators=[
            validators.RegexValidator(r'^[\w\s.@+:-]+$', _('Enter a valid oauth secret.'), 'invalid'),
        ])
    _persist_params = models.TextField(_('persistent parameters'), blank=True, null=True, default=None,
        help_text=_('List of parameters sent by the LTI producer to this application, '
                    'which should be preserved during authentication. Put each parameter name on a new line.'),
        )

    is_default = UniqueBooleanField(help_text=_('Optional. Cohort to use for non-authenticated users. '
                                                'Only one Cohort can be the default.'))

    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    modified_at = models.DateTimeField(auto_now=True, editable=False)

    def _persist_params_list(self):
        params = []
        if self._persist_params:
            params = re.split("[\n\r]+", self._persist_params)
        return params

    persist_params = property(_persist_params_list)

    class CohortManager(models.Manager):

        def get_current(self, user=None):
            '''Return the user's cohort, if set;
               or the default cohort, if found in the database;
               or a cohort constructed from ADELAIDEX_LTI settings, if found;
               or None all else fails.'''

            current = None

            if user and hasattr(user, 'cohort'):
                current = user.cohort

            if not current:
                default = self.filter(is_default=True)
                if default:
                    current = default[0]

            if not current:
                lti_settings = getattr(settings, 'ADELAIDEX_LTI', {})
                lti_oauth = getattr(settings, 'LTI_OAUTH_CREDENTIALS', {})
                if lti_settings or lti_oauth:
                    oauth_key = None
                    oauth_secret = None
                    if lti_oauth:
                        oauth_key = lti_oauth.keys()[0]
                        oauth_secret = lti_oauth[oauth_key]

                    current = Cohort(
                        title=lti_settings.get('LINK_TEXT'),
                        login_url=lti_settings.get('LOGIN_URL'),
                        enrol_url=lti_settings.get('ENROL_URL'),
                        _persist_params="\n".join(lti_settings.get('PERSIST_PARAMS', [])),
                        oauth_key=oauth_key,
                        oauth_secret=oauth_secret,
                        is_default=True,
                    )
                
            return current

    objects = CohortManager()

    def __unicode__(self):
        return '%s (%s)' % (self.title, self.oauth_key)

    def __str__(self):
        return unicode(self).encode('utf-8')


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
    first_name = NullableCharField(_('nickname'), max_length=255,
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

    cohort = models.ForeignKey(Cohort, blank=True, null=True, default=None)

    objects = UserManager()

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['first_name']

    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')
        unique_together = ('first_name', 'cohort',)
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
    '''user.is_staff determines membership in ADELAIDEX_LTI_STAFF_MEMBER_GROUP'''
    staff_group = getattr(settings, 'ADELAIDEX_LTI_STAFF_MEMBER_GROUP')
    if staff_group:
        if instance.is_staff:
            try:
                with transaction.atomic():
                    instance.groups.add(staff_group)
            except IntegrityError:
                # something is wrong with my user_groups migration
                pass
        else:
            instance.groups.remove(staff_group)


class UserForm(ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'time_zone', 'cohort', ]
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

        duplicate = User.objects.filter(cohort=self.instance.cohort,
            first_name=first_name).exclude(id=self.instance.id)
        if duplicate.exists():
            raise ValidationError('Someone with this nickname already exists in your cohort. '
                                  'Please try a different nickname.')
        return first_name
