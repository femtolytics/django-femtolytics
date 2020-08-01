import json
import uuid

from datetime import timedelta
from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone
from femtolytics.models import App, Activity, Session, Visitor

User = get_user_model()

class ActionApiTestCase(TestCase):
    def setUp(self):
        self.package_name = 'com.femtolytics.test'
        self.owner = User.objects.create_user(
            'john',
            'lennon@thebeatles.com',
            'johnpassword')
        self.app = App.objects.create(
            owner=self.owner,
            package_name=self.package_name,
        )
        self.client = Client()
        self.now = timezone.now()
        self.visitor_id = str(uuid.uuid4())

    def test_empty(self):
        response = self.client.post(reverse('femtolytics_api:action'))
        self.assertEqual(response.status_code, 400)

    def test_invalid_body(self):
        message = {}
        response = self.client.post(reverse('femtolytics_api:action'), json.dumps(
            message), content_type='application/json')
        self.assertEqual(response.status_code, 400)

    def test_no_actions(self):
        message = {
            'actions': [],
        }
        response = self.client.post(reverse('femtolytics_api:action'), json.dumps(
            message), content_type='application/json')
        self.assertEqual(response.status_code, 200)

    def test_invalid_action_missing_type_and_time(self):
        message = {
            'actions': [
                {
                    'action': {},
                },
            ],
        }
        response = self.client.post(reverse('femtolytics_api:action'), json.dumps(
            message), content_type='application/json')
        self.assertEqual(response.status_code, 400)

    def test_invalid_action_missing_time(self):
        message = {
            'actions': [
                {
                    'action': {
                        'type': 'VIEW',
                    },
                },
            ],
        }
        response = self.client.post(reverse('femtolytics_api:action'), json.dumps(
            message), content_type='application/json')
        self.assertEqual(response.status_code, 400)

    def test_invalid_action_invalid_time(self):
        message = {
            'actions': [
                {
                    'action': {
                        'type': 'VIEW',
                        'time': 1234567890,
                    },
                    'device': {
                        'name': 'iPhone',
                        'os': 'iOS 1.0.0',
                    },
                    'package': {
                        'name': self.package_name,
                        'version': '1.0.0',
                        'build': '99',
                    },
                    'visitor_id': self.visitor_id,
                },
            ],
        }
        response = self.client.post(reverse('femtolytics_api:action'), json.dumps(
            message), content_type='application/json')
        self.assertEqual(response.status_code, 400)

        message = {
            'actions': [
                {
                    'action': {
                        'type': 'VIEW',
                        'time': 'ABCDEFG',
                    },
                    'device': {
                        'name': 'iPhone',
                        'os': 'iOS 1.0.0',
                    },
                    'package': {
                        'name': self.package_name,
                        'version': '1.0.0',
                        'build': '99',
                    },
                    'visitor_id': self.visitor_id,
                },
            ],
        }
        response = self.client.post(reverse('femtolytics_api:action'), json.dumps(
            message), content_type='application/json')
        self.assertEqual(response.status_code, 400)

    def test_invalid_action_missing_package(self):
        message = {
            'actions': [
                {
                    'action': {
                        'type': 'VIEW',
                        'time': self.now.isoformat(),
                    },
                    'device': {
                        'name': 'iPhone',
                        'os': 'iOS 1.0.0',
                    },
                    'visitor_id': self.visitor_id,
                },
            ],
        }
        response = self.client.post(reverse('femtolytics_api:action'), json.dumps(
            message), content_type='application/json')
        self.assertEqual(response.status_code, 400)

    def test_invalid_action_incomplete_package(self):
        message = {
            'actions': [
                {
                    'action': {
                        'type': 'VIEW',
                        'time': self.now.isoformat(),
                    },
                    'package': {
                        'name': self.package_name,
                    },
                    'device': {
                        'name': 'iPhone',
                        'os': 'iOS 1.0.0',
                    },
                    'visitor_id': self.visitor_id,
                },
            ],
        }
        response = self.client.post(reverse('femtolytics_api:action'), json.dumps(
            message), content_type='application/json')
        self.assertEqual(response.status_code, 400)

    def test_invalid_action_missing_device(self):
        message = {
            'actions': [
                {
                    'action': {
                        'type': 'VIEW',
                        'time': self.now.isoformat(),
                    },
                    'package': {
                        'name': self.package_name,
                        'version': '1.0.0',
                        'build': '99',
                    },
                    'visitor_id': self.visitor_id,
                },
            ],
        }
        response = self.client.post(reverse('femtolytics_api:action'), json.dumps(
            message), content_type='application/json')
        self.assertEqual(response.status_code, 400)

    def test_invalid_action_incomplete_device(self):
        message = {
            'actions': [
                {
                    'action': {
                        'type': 'VIEW',
                        'time': self.now.isoformat(),
                    },
                    'package': {
                        'name': self.package_name,
                        'version': '1.0.0',
                        'build': '99',
                    },
                    'device': {
                        'name': 'iPhone',
                    },
                    'visitor_id': self.visitor_id,
                },
            ],
        }
        response = self.client.post(reverse('femtolytics_api:action'), json.dumps(
            message), content_type='application/json')
        self.assertEqual(response.status_code, 400)

    def test_missing_visitor_id(self):
        message = {
            'actions': [
                {
                    'action': {
                        'type': 'VIEW',
                        'time': self.now.isoformat(),
                        'properties': {
                            'name': 'Landing Page',
                        },
                    },
                    'device': {
                        'name': 'iPhone',
                        'os': 'iOS 1.0.0',
                    },
                    'package': {
                        'name': self.package_name,
                        'version': '1.0.0',
                        'build': '99',
                    },
                },
            ],
        }
        response = self.client.post(reverse('femtolytics_api:action'), json.dumps(
            message), content_type='application/json')
        self.assertEqual(response.status_code, 400)

    def test_invalid_visitor_id(self):
        message = {
            'actions': [
                {
                    'action': {
                        'type': 'VIEW',
                        'time': self.now.isoformat(),
                        'properties': {
                            'name': 'Landing Page',
                        },
                    },
                    'device': {
                        'name': 'iPhone',
                        'os': 'iOS 1.0.0',
                    },
                    'package': {
                        'name': self.package_name,
                        'version': '1.0.0',
                        'build': '99',
                    },
                    'visitor_id': 'ABCD',
                },
            ],
        }
        response = self.client.post(reverse('femtolytics_api:action'), json.dumps(
            message), content_type='application/json')
        self.assertEqual(response.status_code, 400)

    def test_non_registered_app(self):
        message = {
            'actions': [
                {
                    'action': {
                        'type': 'VIEW',
                        'time': self.now.isoformat(),
                    },
                    'device': {
                        'name': 'iPhone',
                        'os': 'iOS 1.0.0',
                    },
                    'package': {
                        'name': 'com.example.app',
                        'version': '1.0.0',
                        'build': '99',
                    },
                    'visitor_id': self.visitor_id,
                },
            ],
        }
        response = self.client.post(reverse('femtolytics_api:action'), json.dumps(
            message), content_type='application/json')
        self.assertEqual(response.status_code, 404)

    def test_valid_action(self):
        message = {
            'actions': [
                {
                    'action': {
                        'type': 'VIEW',
                        'time': self.now.isoformat(),
                        'properties': {
                            'name': 'Landing Page',
                        },
                    },
                    'device': {
                        'name': 'iPhone',
                        'os': 'iOS 1.0.0',
                    },
                    'package': {
                        'name': self.package_name,
                        'version': '1.0.0',
                        'build': '99',
                    },
                    'visitor_id': self.visitor_id,
                },
            ],
        }
        response = self.client.post(reverse('femtolytics_api:action'), json.dumps(
            message), content_type='application/json')
        self.assertEqual(response.status_code, 200)

        qs = Activity.objects.filter(app=self.app, category=Activity.ACTION)
        self.assertEqual(qs.count(), 1)

        action = qs[0]
        self.assertEqual(str(action.visitor_id), self.visitor_id)
        self.assertEqual(action.activity_type, 'VIEW')

        # self.assertEqual(action.session, action.visitor.first_session)

    def test_valid_multiple_action(self):
        message = {
            'actions': [
                {
                    'action': {
                        'type': 'VIEW',
                        'time': self.now.isoformat(),
                        'properties': {
                            'name': 'Landing Page',
                        },
                    },
                    'device': {
                        'name': 'iPhone',
                        'os': 'iOS 1.0.0',
                    },
                    'package': {
                        'name': self.package_name,
                        'version': '1.0.0',
                        'build': '99',
                    },
                    'visitor_id': self.visitor_id,
                },
                {
                    'action': {
                        'type': 'VIEW',
                        'time': (self.now + timedelta(seconds=20)).isoformat(),
                        'properties': {
                            'name': 'Registration Page',
                        },
                    },
                    'device': {
                        'name': 'iPhone',
                        'os': 'iOS 1.0.0',
                    },
                    'package': {
                        'name': self.package_name,
                        'version': '1.0.0',
                        'build': '99',
                    },
                    'visitor_id': self.visitor_id,
                },

            ],
        }
        response = self.client.post(reverse('femtolytics_api:action'), json.dumps(
            message), content_type='application/json')
        self.assertEqual(response.status_code, 200)

        qs = Activity.objects.filter(app=self.app, category=Activity.ACTION)
        self.assertEqual(qs.count(), 2)
