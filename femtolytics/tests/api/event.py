import json
import uuid

from datetime import timedelta
from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone
from femtolytics.models import App, Activity, Crash, Session, Visitor

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
        self.now = timezone.now()
        self.visitor_id = str(uuid.uuid4())

    def test_empty(self):
        response = self.client.post(reverse('femtolytics_api:event'))
        self.assertEqual(response.status_code, 400)

    def test_invalid_body(self):
        message = {}
        response = self.client.post(reverse('femtolytics_api:event'), json.dumps(
            message), content_type='application/json')
        self.assertEqual(response.status_code, 400)

    def test_no_events(self):
        message = {
            'events': [],
        }
        response = self.client.post(reverse('femtolytics_api:event'), json.dumps(
            message), content_type='application/json')
        self.assertEqual(response.status_code, 200)

    def test_invalid_event_missing_type_and_time(self):
        message = {
            'events': [
                {
                    'event': {},
                },
            ],
        }
        response = self.client.post(reverse('femtolytics_api:event'), json.dumps(
            message), content_type='application/json')
        self.assertEqual(response.status_code, 400)

    def test_invalid_event_missing_time(self):
        message = {
            'events': [
                {
                    'event': {
                        'type': 'VIEW',
                    },
                },
            ],
        }
        response = self.client.post(reverse('femtolytics_api:event'), json.dumps(
            message), content_type='application/json')
        self.assertEqual(response.status_code, 400)

    def test_invalid_event_invalid_event(self):
        message = {
            'events': [
                {
                    'event': {
                        'type': 'ABC',
                        'time': self.now.isoformat(),
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
        response = self.client.post(reverse('femtolytics_api:event'), json.dumps(
            message), content_type='application/json')
        self.assertEqual(response.status_code, 400)

    def test_invalid_event_invalid_time(self):
        message = {
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
        response = self.client.post(reverse('femtolytics_api:event'), json.dumps(
            message), content_type='application/json')
        self.assertEqual(response.status_code, 400)

        message = {
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
        response = self.client.post(reverse('femtolytics_api:event'), json.dumps(
            message), content_type='application/json')
        self.assertEqual(response.status_code, 400)

    def test_invalid_event_missing_package(self):
        message = {
            'events': [
                {
                    'event': {
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
        response = self.client.post(reverse('femtolytics_api:event'), json.dumps(
            message), content_type='application/json')
        self.assertEqual(response.status_code, 400)

    def test_invalid_event_incomplete_package(self):
        message = {
            'events': [
                {
                    'event': {
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
        response = self.client.post(reverse('femtolytics_api:event'), json.dumps(
            message), content_type='application/json')
        self.assertEqual(response.status_code, 400)

    def test_invalid_event_missing_device(self):
        message = {
            'events': [
                {
                    'event': {
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
        response = self.client.post(reverse('femtolytics_api:event'), json.dumps(
            message), content_type='application/json')
        self.assertEqual(response.status_code, 400)

    def test_invalid_event_incomplete_device(self):
        message = {
            'events': [
                {
                    'event': {
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
        response = self.client.post(reverse('femtolytics_api:event'), json.dumps(
            message), content_type='application/json')
        self.assertEqual(response.status_code, 400)

    def test_missing_visitor_id(self):
        message = {
            'events': [
                {
                    'event': {
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
        response = self.client.post(reverse('femtolytics_api:event'), json.dumps(
            message), content_type='application/json')
        self.assertEqual(response.status_code, 400)

    def test_invalid_visitor_id(self):
        message = {
            'events': [
                {
                    'event': {
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
        response = self.client.post(reverse('femtolytics_api:event'), json.dumps(
            message), content_type='application/json')
        self.assertEqual(response.status_code, 400)

    def test_non_registered_app(self):
        message = {
            'events': [
                {
                    'event': {
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
        response = self.client.post(reverse('femtolytics_api:event'), json.dumps(
            message), content_type='application/json')
        self.assertEqual(response.status_code, 404)

    def test_valid_event(self):
        message = {
            'events': [
                {
                    'event': {
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
        response = self.client.post(reverse('femtolytics_api:event'), json.dumps(
            message), content_type='application/json')
        self.assertEqual(response.status_code, 200)

        qs = Activity.objects.filter(app=self.app, category=Activity.EVENT)
        self.assertEqual(qs.count(), 1)

        event = qs[0]
        self.assertEqual(str(event.visitor_id), self.visitor_id)
        self.assertEqual(event.activity_type, 'VIEW')
        self.assertEqual(event.session, event.visitor.first_session)

    def test_valid_multiple_event(self):
        message = {
            'events': [
                {
                    'event': {
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
                    'event': {
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
        response = self.client.post(reverse('femtolytics_api:event'), json.dumps(
            message), content_type='application/json')
        self.assertEqual(response.status_code, 200)

        qs = Activity.objects.filter(app=self.app, category=Activity.EVENT)
        self.assertEqual(qs.count(), 2)


    def test_crash(self):
        message = {
            'events': [
                {
                    'event': {
                        'type': 'CRASH',
                        'time': self.now.isoformat(),
                        'properties': {
                            'exception': "DatabaseException(Error Domain=FMDatabase Code=2067 \"UNIQUE constraint failed: payees.name\" UserInfo={NSLocalizedDescription=UNIQUE constraint failed: payees.name}) sql 'INSERT INTO payees (name, system, local) VALUES (?, ?, ?)' args [Withdrawal Online Transfer to 0945, 0, 0]}",
                            'stack_trace': "#0 wrapDatabaseException (package:sqflite/src/exception_impl.dart:11)\n<asynchronous suspension>\n#1 BasicLock.synchronized (package:synchronized/src/basic_lock.dart:34)\n<asynchronous suspension>\n#2 SqfliteDatabaseMixin.txnSynchronized (package:sqflite_common/src/database_mixin.dart:337)\n<asynchronous suspension>\n#3 PayeeDao.insert (package:instabudget/models/payee_dao.dart:46)\n<asynchronous suspension>\n#4 Portafilter.upsertPlaidTransaction (package:instabudget/models/portafilter.dart:342)\n<asynchronous suspension>\n#5 Synchronizer.synchronize.<anonymous closure> (package:instabudget/utils/synchronizer.dart:100)\n<asynchronous suspension>\n",
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
        response = self.client.post(reverse('femtolytics_api:event'), json.dumps(
            message), content_type='application/json')
        self.assertEqual(response.status_code, 200)

        qs = Activity.objects.filter(app=self.app, category=Activity.EVENT)
        self.assertEqual(qs.count(), 1)

        event = qs[0]
        self.assertEqual(str(event.visitor_id), self.visitor_id)
        self.assertEqual(event.activity_type, 'CRASH')
        self.assertEqual(event.session, event.visitor.first_session)

        qs = Crash.objects.filter(app=self.app)
        self.assertEqual(qs.count(), 1)
        crash = qs[0]
        self.assertEqual(crash.first_at, self.now)
        self.assertEqual(crash.last_at, self.now)

        # Make sure we find the same signature
        then = self.now + timedelta(hours=2)
        message = {
            'events': [
                {
                    'event': {
                        'type': 'CRASH',
                        'time': then.isoformat(),
                        'properties': {
                            'exception': "DatabaseException(Error Domain=FMDatabase Code=2067 \"UNIQUE constraint failed: payees.name\" UserInfo={NSLocalizedDescription=UNIQUE constraint failed: payees.name}) sql 'INSERT INTO payees (name, system, local) VALUES (?, ?, ?)' args [REI.COM, 0, 0]}",
                            'stack_trace': "#0 wrapDatabaseException (package:sqflite/src/exception_impl.dart:11)\n<asynchronous suspension>\n#1 BasicLock.synchronized (package:synchronized/src/basic_lock.dart:34)\n<asynchronous suspension>\n#2 SqfliteDatabaseMixin.txnSynchronized (package:sqflite_common/src/database_mixin.dart:337)\n<asynchronous suspension>\n#3 PayeeDao.insert (package:instabudget/models/payee_dao.dart:46)\n<asynchronous suspension>\n#4 Portafilter.upsertPlaidTransaction (package:instabudget/models/portafilter.dart:342)\n<asynchronous suspension>\n#5 Synchronizer.synchronize.<anonymous closure> (package:instabudget/utils/synchronizer.dart:100)\n<asynchronous suspension>\n",
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
        response = self.client.post(reverse('femtolytics_api:event'), json.dumps(
            message), content_type='application/json')
        self.assertEqual(response.status_code, 200)

        qs = Crash.objects.filter(app=self.app)
        self.assertEqual(qs.count(), 1)
        crash = qs[0]
        self.assertEqual(crash.sessions.count(), 2)
        self.assertEqual(crash.activities.count(), 2)
        self.assertEqual(crash.first_at, self.now)
        self.assertEqual(crash.last_at, then)
