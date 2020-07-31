import json
import uuid

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from femtolytics.models import App, Activity

User = get_user_model()

class EventApiTestCase(TestCase):
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
        self.visitor_id = str(uuid.uuid4())

    def test_empty(self):
        response = self.client.post(reverse('femtolytics_api:event'))
        self.assertEqual(response.status_code, 400)
    
    def test_invalid_body(self):
        message= {}
        response = self.client.post(reverse('femtolytics_api:event'), json.dumps(message), content_type='application/json')
        self.assertEqual(response.status_code, 400)

    def test_no_events(self):
        message= {
            'events': [],
        }
        response = self.client.post(reverse('femtolytics_api:event'), json.dumps(message), content_type='application/json')
        self.assertEqual(response.status_code, 200)

    def test_invalid_event_missing_type_and_time(self):
        message= {
            'events': [
                {
                    'event': {},
                },
            ],
        }
        response = self.client.post(reverse('femtolytics_api:event'), json.dumps(message), content_type='application/json')
        self.assertEqual(response.status_code, 400)

    def test_invalid_event_missing_time(self):
        message= {
            'events': [
                {
                    'event': {
                        'type': 'VIEW',
                    },
                },
            ],
        }
        response = self.client.post(reverse('femtolytics_api:event'), json.dumps(message), content_type='application/json')
        self.assertEqual(response.status_code, 400)

    def test_invalid_event_invalid_event(self):
        message= {
            'events': [
                {
                    'event': {
                        'type': 'ABC',
                        'time': '2020-07-31T17:15:05.358216',
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
        response = self.client.post(reverse('femtolytics_api:event'), json.dumps(message), content_type='application/json')
        self.assertEqual(response.status_code, 400)


    def test_invalid_event_invalid_time(self):
        message= {
            'events': [
                {
                    'event': {
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
        response = self.client.post(reverse('femtolytics_api:event'), json.dumps(message), content_type='application/json')
        self.assertEqual(response.status_code, 400)

        message= {
            'events': [
                {
                    'event': {
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
        response = self.client.post(reverse('femtolytics_api:event'), json.dumps(message), content_type='application/json')
        self.assertEqual(response.status_code, 400)

    def test_non_registered_app(self):
        message= {
            'events': [
                {
                    'event': {
                        'type': 'VIEW',
                        'time': '2020-07-31T17:15:05.358216',
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
        response = self.client.post(reverse('femtolytics_api:event'), json.dumps(message), content_type='application/json')
        self.assertEqual(response.status_code, 404)

    def test_valid_event(self):
        message= {
            'events': [
                {
                    'event': {
                        'type': 'VIEW',
                        'time': '2020-07-31T17:15:05.358216',
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
        response = self.client.post(reverse('femtolytics_api:event'), json.dumps(message), content_type='application/json')
        self.assertEqual(response.status_code, 200)
        
        qs = Activity.objects.filter(app=self.app, category=Activity.EVENT)
        self.assertEqual(qs.count(), 1)
        
        event = qs[0]
        self.assertEqual(str(event.visitor_id), self.visitor_id)
        self.assertEqual(event.activity_type, 'VIEW')

        # self.assertEqual(event.session, event.visitor.first_session)
