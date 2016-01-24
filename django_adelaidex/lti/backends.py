from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend
from django.core.exceptions import PermissionDenied

from ims_lti_py.tool_provider import DjangoToolProvider
from time import time
import sys
import logging

logger = logging.getLogger(__name__)

from django.conf import settings
from django_auth_lti.backends import LTIAuthBackend
from django_adelaidex.lti.models import Cohort


class CohortLTIAuthBackend(LTIAuthBackend):

    """
    By default, the ``authenticate`` method creates ``User`` objects for
    usernames that don't already exist in the database, and assigns them to an appropriate Cohort.
    Subclasses can disable this behavior by setting the ``create_unknown_user``
    attribute to ``False``.
    """

    # Create a User object if not already in the database?
    create_unknown_user = True
    # Username prefix for users without an sis source id
    unknown_user_prefix = "cuid:"

    def authenticate(self, request):

        logger.info("about to begin authentication process")

        request_key = request.POST.get('oauth_consumer_key', None)

        if request_key is None:
            logger.error("Request doesn't contain an oauth_consumer_key; can't continue.")
            return None

        oauth_credentials = getattr(settings, 'LTI_OAUTH_CREDENTIALS', {})
        cohorts = Cohort.objects.filter(oauth_key=request_key).all()
        cohort = None
        if cohorts:
            cohort = cohorts[0]

        # Let settings.LTI_OAUTH_CREDENTIALS secret override the database cohort secret
        secret = oauth_credentials.get(request_key)
        if secret is None and cohort:
            secret = cohort.oauth_secret

        if secret is None:
            logger.error("Could not get a secret for key %s" % request_key)
            raise PermissionDenied

        logger.debug('using key/secret %s/%s' % (request_key, secret))
        tool_provider = DjangoToolProvider(request_key, secret, request.POST.dict())

        postparams = request.POST.dict()

        logger.debug('request is secure: %s' % request.is_secure())
        for key in postparams:
            logger.debug('POST %s: %s' % (key, postparams.get(key)))

        logger.debug('request abs url is %s' % request.build_absolute_uri())

        for key in request.META:
            logger.debug('META %s: %s' % (key, request.META.get(key)))

        logger.info("about to check the signature")

        valid = False
        try:
            valid = tool_provider.is_valid_request(request)
        except:
            logger.error(str(sys.exc_info()[0]))
            valid = False
        finally:
            if not valid:
                logger.error("Invalid request: signature check failed.")
                raise PermissionDenied

        logger.info("done checking the signature")

        logger.info("about to check the timestamp: %d" % int(tool_provider.oauth_timestamp))
        if time() - int(tool_provider.oauth_timestamp) > 60 * 60:
            logger.error("OAuth timestamp is too old.")
            #raise PermissionDenied
        else:
            logger.info("timestamp looks good")

        logger.info("done checking the timestamp")

        # (this is where we should check the nonce)

        # if we got this far, the user is good

        user = None

        # Retrieve username from LTI parameter or default to an overridable function return value
        username = tool_provider.lis_person_sourcedid or self.get_default_username(
            tool_provider, prefix=self.unknown_user_prefix)
        username = self.clean_username(username)  # Clean it

        email = tool_provider.lis_person_contact_email_primary
        first_name = tool_provider.lis_person_name_given
        last_name = tool_provider.lis_person_name_family

        logger.info("We have a valid username: %s" % username)

        UserModel = get_user_model()

        # Note that this could be accomplished in one try-except clause, but
        # instead we use get_or_create when creating unknown users since it has
        # built-in safeguards for multiple threads.
        if self.create_unknown_user:
            user, created = UserModel.objects.get_or_create(**{
                UserModel.USERNAME_FIELD: username,
            })

            if created:
                logger.debug('authenticate created a new user for %s' % username)
            else:
                logger.debug('authenticate found an existing user for %s' % username)

        else:
            logger.debug(
                'automatic new user creation is turned OFF! just try to find and existing record')
            try:
                user = UserModel.objects.get_by_natural_key(username)
            except UserModel.DoesNotExist:
                logger.debug('authenticate could not find user %s' % username)
                # should return some kind of error here?
                pass

        # update the user
        if cohort:
            user.cohort = cohort
        if email:
            user.email = email
        # FIXME ADX-192: should really be using our own nickname field, instead
        # of requiring first_name to be unique.
        #if first_name:
        #    user.first_name = first_name
        if last_name:
            user.last_name = last_name
        user.save()
        logger.debug("updated the user record in the database")

        return user
