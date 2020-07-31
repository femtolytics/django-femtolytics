import json
import uuid

from datetime import timedelta
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from femtolytics.models import App, Activity, Session, Visitor

User = get_user_model()


class FindAppVisitorSessionTestCase(TestCase):
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
        self.now = timezone.now()
        self.visitor_id = str(uuid.uuid4())

    def test_app_not_found(self):
        evt = {
            'package': {
                'name': 'com.example.app',
            }
        }
        app, visitor, session = Activity.find_app_visitor_session(evt)
        self.assertEqual(app, None)

    def test_all_new(self):
        evt = {
            'package': {
                'name': self.package_name,
            },
            'event_time': self.now,
            'visitor_id': self.visitor_id,
        }
        app, visitor, session = Activity.find_app_visitor_session(evt)
        self.assertEqual(app, self.app)
        self.assertEqual(visitor.id, self.visitor_id)
        self.assertEqual(visitor.registered_at, self.now)
        self.assertIsNotNone(session)
        self.assertEqual(session.started_at, self.now)

    def test_rewind_times(self):
        # Make sure visitor.registered_at and session.started_at are rewinded properly
        visitor = Visitor.objects.create(
            id=self.visitor_id,
            app=self.app,
            registered_at=self.now + timedelta(hours=1),
        )
        session = Session.objects.create(
            app=self.app,
            visitor=visitor,
            started_at=self.now + timedelta(minutes=10),
            ended_at=self.now + timedelta(minutes=15),
        )
        evt = {
            'package': {
                'name': self.package_name,
            },
            'event_time': self.now,
            'visitor_id': self.visitor_id,
        }
        _, v, s = Activity.find_app_visitor_session(evt)
        self.assertEqual(str(v.id), visitor.id)
        self.assertEqual(s.id, session.id)
        self.assertEqual(v.registered_at, self.now, 'Visitor registration time was not updated')
        self.assertEqual(s.started_at, self.now, 'Session started at was not updated')

    def test_create_new_session_even_with_existing(self):
        visitor = Visitor.objects.create(
            id=self.visitor_id,
            app=self.app,
            registered_at=self.now - timedelta(hours=12),
        )
        session = Session.objects.create(
            app=self.app,
            visitor=visitor,
            started_at=self.now - timedelta(hours=12),
            ended_at=self.now - timedelta(hours=10),
        )

        evt = {
            'package': {
                'name': self.package_name,
            },
            'event_time': self.now - timedelta(hours=8),
            'visitor_id': self.visitor_id,
        }
        _, v, s = Activity.find_app_visitor_session(evt)
        self.assertEqual(str(v.id), visitor.id)
        self.assertNotEqual(s.id, session.id)

    def test_find_nearby_session(self):
        visitor = Visitor.objects.create(
            id=self.visitor_id,
            app=self.app,
            registered_at=self.now,
        )
        session = Session.objects.create(
            app=self.app,
            visitor=visitor,
            started_at=self.now,
            ended_at=self.now + timedelta(minutes=10),
        )

        event_time = self.now + timedelta(minutes=15)
        evt = {
            'package': {
                'name': self.package_name,
            },
            'event_time': event_time,
            'visitor_id': self.visitor_id,
        }
        _, v, s = Activity.find_app_visitor_session(evt)
        self.assertEqual(str(v.id), visitor.id)
        self.assertEqual(s.id, session.id)
        self.assertEqual(s.ended_at, event_time, "Session ended_at was not extended")


    def test_find_correct_session(self):
        # Make sure old events is being matched to corresponding session
        visitor = Visitor.objects.create(
            id=self.visitor_id,
            app=self.app,
            registered_at=self.now - timedelta(hours=12),
        )
        session1 = Session.objects.create(
            app=self.app,
            visitor=visitor,
            started_at=self.now - timedelta(hours=12),
            ended_at=self.now - timedelta(hours=10),
        )
        session2 = Session.objects.create(
            app=self.app,
            visitor=visitor,
            started_at=self.now - timedelta(hours=1),
            ended_at=self.now + timedelta(hours=1),
        )

        evt = {
            'package': {
                'name': self.package_name,
            },
            'event_time': self.now - timedelta(hours=11),
            'visitor_id': self.visitor_id,
        }
        _, v, s = Activity.find_app_visitor_session(evt)
        self.assertEqual(str(v.id), visitor.id)
        self.assertEqual(s.id, session1.id)


    def test_session_gap_detection(self):
        visitor = Visitor.objects.create(
            id=self.visitor_id,
            app=self.app,
            registered_at=self.now,
        )
        session = Session.objects.create(
            app=self.app,
            visitor=visitor,
            started_at=self.now,
            ended_at=self.now + timedelta(minutes=10),
        )

        # Session is [now, now + 10m]
        # Event is now + 15m, so it should fall into session
        event_time = self.now + timedelta(minutes=15)
        evt = {
            'package': {
                'name': self.package_name,
            },
            'event_time': event_time,
            'visitor_id': self.visitor_id,
        }
        _, v, s = Activity.find_app_visitor_session(evt)
        self.assertEqual(str(v.id), visitor.id)
        self.assertEqual(s.id, session.id)
        self.assertEqual(s.ended_at, event_time, "Session ended_at was not extended")

        # Session is [now, now + 15m]
        # Gap is 15m, event is now + 31m, it should create a new session
        event_time = self.now + timedelta(minutes=31)
        evt = {
            'package': {
                'name': self.package_name,
            },
            'event_time': event_time,
            'visitor_id': self.visitor_id,
        }
        _, v, s = Activity.find_app_visitor_session(evt, session_gap_seconds=900)
        self.assertEqual(str(v.id), visitor.id)
        self.assertNotEqual(s.id, session.id)


