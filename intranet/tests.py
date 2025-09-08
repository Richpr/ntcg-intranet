# intranet/tests.py
from django.test import TestCase
from django.contrib.auth import get_user_model
from .models import Notification

User = get_user_model()

class NotificationModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser', 
            password='testpassword'
        )

    def test_notification_creation(self):
        notification = Notification.objects.create(
            recipient=self.user,
            title='Nouvelle notification',
            message='Ceci est un test de notification.',
        )
        self.assertEqual(notification.recipient, self.user)
        self.assertEqual(notification.title, 'Nouvelle notification')
        self.assertFalse(notification.is_read)
        self.assertEqual(notification.type, 'info')

    def test_mark_as_read(self):
        notification = Notification.objects.create(
            recipient=self.user,
            title='Test',
            message='Test',
        )
        notification.is_read = True
        notification.save()
        self.assertTrue(notification.is_read)