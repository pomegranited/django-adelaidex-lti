from django.test import TestCase
from django.core import mail
from django.core.management import call_command

from django_adelaidex.lti.models import User, UserManager, UserForm, staff_member_group

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


class UserGroupTests(TestCase):

    @classmethod
    def setUpClass(cls):
        # Load staff group fixtures data
        call_command("loaddata", '000_staff_group.json', verbosity=0)
        super(UserGroupTests, cls).setUpClass()

    def test_staff_group(self):
        '''Ensure user.is_staff determines membership in Staff Members group'''
        user = User.objects.create_user('user_name')
        group_id = staff_member_group()

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

        user = User.objects.create_user('user1', first_name='First')
        user.save()

        # User first_name must be unique
        form = UserForm(data={'first_name': user.first_name})
        self.assertFalse(form.is_valid())

        form = UserForm(data={'first_name': 'something-else'})
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
