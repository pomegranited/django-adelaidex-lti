from django.test import TestCase
from django.core import mail
from django.core.management import call_command
from django.contrib.auth.models import AnonymousUser
from django.test.utils import override_settings
from django.conf import settings
from django.db import IntegrityError
from mock import Mock

from django_adelaidex.lti.models import Cohort, User, UserManager, UserForm


class CohortManagerTests(TestCase):

    def test_no_default(self):
        cohort = Cohort.objects.get_current()
        self.assertIsNone(cohort)

    @override_settings(ADELAIDEX_LTI={
        'LINK_TEXT': 'Link Text',
        'LOGIN_URL': 'https://google.com',
        'ENROL_URL': 'https://google.com/enrol',
    }, LTI_OAUTH_CREDENTIALS={
        'mykey': 'mysecret'
    })
    def test_settings_default(self):
        '''Ensure backwards compatibility'''
        cohort = Cohort.objects.get_current()
        self.assertIsNotNone(cohort)
        self.assertEquals(cohort.title, 'Link Text')
        self.assertEquals(cohort.login_url, 'https://google.com')
        self.assertEquals(cohort.enrol_url, 'https://google.com/enrol')
        self.assertEquals(cohort.persist_params, [])
        self.assertEquals(cohort.is_default, True)
        self.assertEquals(cohort.oauth_key, 'mykey')
        self.assertEquals(cohort.oauth_secret, 'mysecret')

    def test_real_default(self):
        cohort1 = Cohort.objects.create(
            title='Test Cohort',
            oauth_key='mykey',
            oauth_secret='mysecret',
            login_url='http://google.com',
        )
        cohort2 = Cohort.objects.create(
            title='Test Cohort',
            oauth_key='mykey2',
            oauth_secret='mysecret2',
            login_url='http://google.com',
            is_default=True
        )

        cohort = Cohort.objects.get_current()
        self.assertEquals(cohort, cohort2)

        cohort1.is_default = True
        cohort1.save()
        cohort = Cohort.objects.get_current()
        self.assertEquals(cohort, cohort1)

    def test_no_user(self):
        request = Mock()
        request.user = None
        cohort = Cohort.objects.get_current(request.user)
        self.assertIsNone(cohort)

    def test_anonymous_user(self):
        request = Mock()
        request.user = AnonymousUser()
        request.user.is_authenticated = lambda : True
        cohort = Cohort.objects.get_current(request.user)
        self.assertIsNone(cohort)

    def test_authenticated_user(self):
        request = Mock()
        request.user = Mock()
        request.user.is_authenticated = lambda : True
        request.user.cohort = Cohort(
            title='User Cohort',
            oauth_key='mykey',
            oauth_secret='mysecret',
            login_url='http://google.com',
            is_default=True
        )

        cohort = Cohort.objects.get_current(request.user)
        self.assertEquals(cohort, request.user.cohort)


class CohortTests(TestCase):

    def test_str(self):
       
        '''Cohort shows the title and oauth_key'''
        cohort = Cohort.objects.create(
            title='Test Cohort',
            oauth_key='mykey',
            oauth_secret='mysecret',
            login_url='http://google.com',
        )
        self.assertEquals(
            str(cohort),
            'Test Cohort (mykey)'
        )

        cohort.oauth_key = 'mykey2'
        self.assertEquals(
            str(cohort),
            'Test Cohort (mykey2)'
        )
    
    def test_persist_params(self):
        cohort = Cohort.objects.create()
        self.assertEquals(cohort.persist_params, [])

        cohort._persist_params = "abc\ndef\nghi"
        self.assertEquals(cohort.persist_params, ['abc', 'def', 'ghi'])


class UserManagerTests(TestCase):

    def test_create_staffuser(self):
        staff_user = User.objects.create_staffuser('staff_member', password='password')
        self.assertTrue(staff_user.is_staff)
        self.assertFalse(staff_user.is_superuser)

    def test_create_superuser(self):
        super_user = User.objects.create_superuser('super_member', password='password')
        self.assertFalse(super_user.is_staff)
        self.assertTrue(super_user.is_superuser)


class UserTests(TestCase):

    def test_str(self):
       
        '''User string shows first_name if available, else username'''
        user = User.objects.create_user('user_name')
        self.assertEquals(
            str(user),
            'user_name'
        )

        user.first_name = 'NickName'
        self.assertEquals(
            str(user),
            'NickName'
        )

    def test_empty_names_ok(self):
        # Should be able to create users with no first_name
        noname = User.objects.create_user('noname')
        self.assertEquals(noname.get_full_name(), '')

        # ..Without hitting the uniqueness constraint
        noname2 = User.objects.create_user('noname2')
        self.assertEquals(noname.get_full_name(), '')

    def test_full_name(self):
        firstname = User.objects.create_user('firstname', first_name = 'First')
        self.assertEquals(firstname.get_full_name(), firstname.first_name)

        lastname = User.objects.create_user('lastname', last_name = 'Last')
        self.assertEquals(lastname.get_full_name(), lastname.last_name)

        fullname = User.objects.create_user('fullname', first_name='Full', last_name = 'Name')
        self.assertEquals(fullname.get_full_name(), 
                          '%s %s' % (fullname.first_name, fullname.last_name))

        trimname = User.objects.create_user('trimname', first_name=' Trim ', last_name = 'Name ')
        self.assertEquals(trimname.get_full_name(), 
                          ('%s %s' % (trimname.first_name, trimname.last_name)).strip())

    def test_short_name(self):
        noname = User.objects.create_user('noname')
        self.assertEquals(noname.get_short_name(), '')

        firstname = User.objects.create_user('firstname', first_name = 'First')
        self.assertEquals(firstname.get_short_name(), firstname.first_name)

        lastname = User.objects.create_user('lastname', last_name = 'Last')
        self.assertEquals(lastname.get_short_name(), '')

        fullname = User.objects.create_user('fullname', first_name='Full', last_name = 'Name')
        self.assertEquals(fullname.get_short_name(), fullname.first_name)

        trimname = User.objects.create_user('trimname', first_name=' Trim', last_name = 'Name ')
        self.assertEquals(trimname.get_short_name(), trimname.first_name)

    def test_email_user(self):
        # valid send_mail parameters
        kwargs = {
            "fail_silently": False,
            "auth_user": None,
            "auth_password": None,
            "connection": None,
            "html_message": None,
        }
        user = User(email='foo@bar.com')
        user.email_user(subject="Subject here",
            message="This is a message", from_email="from@domain.com", **kwargs)
        # Test that one message has been sent.
        self.assertEqual(len(mail.outbox), 1)
        # Verify that test email contains the correct attributes:
        message = mail.outbox[0]
        self.assertEqual(message.subject, "Subject here")
        self.assertEqual(message.body, "This is a message")
        self.assertEqual(message.from_email, "from@domain.com")
        self.assertEqual(message.to, [user.email])

    def test_name_unique_cohort(self):
        cohort = Cohort.objects.create(
            title='Test Cohort',
            oauth_key='mykey',
            oauth_secret='mysecret',
            login_url='http://google.com',
        )
        user = User.objects.create_user('user1', first_name='First', cohort=cohort)
        self.assertRaises(IntegrityError, User.objects.create_user,
            'user2', first_name='First', cohort=cohort)


class UserGroupTests(TestCase):

    @classmethod
    def setUpClass(cls):
        # Load staff group fixtures data
        call_command("loaddata", '000_staff_group.json', verbosity=0)
        super(UserGroupTests, cls).setUpClass()

    def test_no_staff_group(self):
        '''Ensure user creation works without setting ADELAIDEX_LTI.STAFF_MEMBER_GROUP'''
        user = User.objects.create_user('user_name')
        self.assertEquals(0, user.groups.count())

        # refetch to ensure data not cached
        user = User.objects.get(username='user_name')
        self.assertEquals(0, user.groups.count())

        user.is_staff = True
        user.save()
        user = User.objects.get(username='user_name')
        self.assertEquals(1, user.groups.count())

        user.is_staff = False
        user.save()
        user = User.objects.get(username='user_name')
        self.assertEquals(0, user.groups.count())

        # changing without saving does nothing
        user.is_staff = True
        user = User.objects.get(username='user_name')
        self.assertEquals(0, user.groups.count())

    @override_settings(ADELAIDEX_LTI={'STAFF_MEMBER_GROUP': 1})
    def test_staff_group(self):
        '''Ensure user.is_staff determines membership in Staff Members group'''
        user = User.objects.create_user('user_name')
        group_id = settings.ADELAIDEX_LTI['STAFF_MEMBER_GROUP']

        self.assertEquals(0, user.groups.count())

        # refetch to ensure data not cached
        user = User.objects.get(username='user_name')
        self.assertEquals(0, user.groups.count())

        user.is_staff = True
        user.save()
        user = User.objects.get(username='user_name')
        self.assertEquals(1, user.groups.count())

        user.is_staff = False
        user.save()
        user = User.objects.get(username='user_name')
        self.assertEquals(0, user.groups.filter(id=group_id).count())

        # changing without saving does nothing
        user.is_staff = True
        user = User.objects.get(username='user_name')
        self.assertEquals(0, user.groups.filter(id=group_id).count())


class UserModelFormTests(TestCase):
    """model.UserForm tests."""

    def test_name_required(self):

        # User requires a first_name
        form = UserForm(data={})
        self.assertFalse(form.is_valid())

        # User requires a non-empty first_name
        form = UserForm(data={'first_name': ''})
        self.assertFalse(form.is_valid())

        # User requires a non-empty first_name
        form = UserForm(data={'first_name': '  '})
        self.assertFalse(form.is_valid())

        # User requires a first_name without spaces
        form = UserForm(data={'first_name': 'name goes here'})
        self.assertFalse(form.is_valid())

        # User accepts a single word first name.
        form = UserForm(data={'first_name': 'name_goes@here-or-there.com'})
        self.assertTrue(form.is_valid())

    def test_name_unique(self):

        # Test first_name uniqueness with null cohort
        user = User.objects.create_user('user1', first_name='First')
        user.save()

        form = UserForm(data={'first_name': user.first_name, 'cohort': user.cohort})
        self.assertFalse(form.is_valid())

        form = UserForm(data={'first_name': 'adifferentname', 'cohort': user.cohort})
        self.assertTrue(form.is_valid())

        # Test with a non-null cohort
        cohort = Cohort.objects.create(
            title='Test Cohort',
            oauth_key='mykey',
            oauth_secret='mysecret',
            login_url='http://google.com',
        )
        user.cohort = cohort
        user.save()

        form = UserForm(data={'first_name': user.first_name, 'cohort': user.cohort.id})
        self.assertFalse(form.is_valid())

        form = UserForm(data={'first_name': 'adifferentname', 'cohort': user.cohort.id})
        self.assertTrue(form.is_valid())

        form = UserForm(data={'first_name': user.first_name, 'cohort': None})
        self.assertTrue(form.is_valid())

    def test_time_zone(self):

        # Time zone not required
        data = {'first_name': 'name_goes@here-or-there.com'}
        form = UserForm(data=data)
        self.assertTrue(form.is_valid())

        # Invalid time zones are allowed (enforced by form Widget, not Model)
        data['time_zone'] = 'NOT A TIME ZONE'
        form = UserForm(data=data)
        self.assertTrue(form.is_valid())

        # Valid time zone allowed
        data['time_zone'] = 'Australia/Adelaide'
        form = UserForm(data=data)
        self.assertTrue(form.is_valid())
