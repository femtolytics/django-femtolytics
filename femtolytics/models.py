import json
import logging
import uuid

from datetime import datetime, timedelta
from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()

logger = logging.getLogger("femtolytics")

class BaseModel(models.Model):
    id = models.UUIDField(primary_key=True, editable=False, default=uuid.uuid4)
    created_at = models.DateTimeField(
        auto_now_add=True, editable=False, db_index=True)
    modified_at = models.DateTimeField(auto_now=True, editable=False)

    @property
    def short_id(self):
        return str(self.id)[:8]

    class Meta:
        abstract = True


class App(BaseModel):
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    package_name = models.CharField(max_length=255, db_index=True)


class Visitor(BaseModel):
    registered_at = models.DateTimeField(default=datetime.now)
    app = models.ForeignKey(App, on_delete=models.CASCADE)


class Session(BaseModel):
    visitor = models.ForeignKey(Visitor, on_delete=models.CASCADE)
    app = models.ForeignKey(App, on_delete=models.CASCADE)
    started_at = models.DateTimeField(default=datetime.now)
    ended_at = models.DateTimeField()

    @property
    def duration_str(self):
        seconds = int(self.duration.total_seconds())
        periods = [
            ('year',        60*60*24*365),
            ('month',       60*60*24*30),
            ('day',         60*60*24),
            ('hour',        60*60),
            ('minute',      60),
            ('second',      1)
        ]

        strings = []
        for period_name, period_seconds in periods:
            if seconds > period_seconds:
                period_value, seconds = divmod(seconds, period_seconds)
                has_s = 's' if period_value > 1 else ''
                strings.append("%s %s%s" % (period_value, period_name, has_s))

        return ", ".join(strings)

    @property
    def duration(self):
        return self.ended_at - self.started_at

    @property
    def sorted_activities(self):
        return self.activity_set.order_by('-occured_at')


class Activity(BaseModel):
    EVENT = 'E'
    ACTION = 'A'
    TYPES = [
        (EVENT, 'Event'),
        (ACTION, 'Action'),
    ]
    visitor = models.ForeignKey(Visitor, on_delete=models.CASCADE)
    session = models.ForeignKey(Session, on_delete=models.CASCADE)
    app = models.ForeignKey(App, on_delete=models.CASCADE)
    category = models.CharField(max_length=1, choices=TYPES, db_index=True)
    activity_type = models.CharField(max_length=255, db_index=True)
    properties = models.TextField(null=True, default=None, blank=True)
    occured_at = models.DateTimeField(db_index=True)
    device_name = models.CharField(max_length=255, db_index=True)
    device_os = models.CharField(max_length=255, db_index=True)
    package_name = models.CharField(max_length=255, db_index=True)
    package_version = models.CharField(max_length=255, db_index=True)
    package_build = models.CharField(max_length=255)

    remote_ip = models.CharField(
        max_length=255, blank=True, null=True, default=None)
    city = models.CharField(max_length=255, blank=True,
                            null=True, default=None)
    region = models.CharField(
        max_length=255, blank=True, null=True, default=None)
    country = models.CharField(
        max_length=255, blank=True, null=True, default=None)

    @property
    def version(self):
        return f"{self.package_version}.{self.package_build}"

    @property
    def device(self):
        return f"{self.device_name} {self.device_os}"

    @property
    def location(self):
        return f"{self.city} {self.country}" if self.city is not None else ""

    @property
    def analyzed_type(self):
        return self.activity_type

    @property
    def analyzed_properties(self):
        if self.properties is None:
            return None
        props = json.loads(self.properties)
        if self.category == Activity.EVENT:
            if self.activity_type == 'VIEW':
                return props['view']
            elif self.activity_type == 'NEW_USER':
                return props['visitor_id']
            elif self.activity_type == 'CRASH':
                return props['exception']
        return json.dumps(props, indent=2, sort_keys=True)

    @property
    def extended_properties(self):
        if self.properties is None:
            return None
        props = json.loads(self.properties)
        if self.category == Activity.EVENT:
            if self.activity_type == 'CRASH':
                return props['stack_trace']
        return None

    @classmethod
    def find_app_visitor_session(cls, event_or_action):
        app = None
        try:
            app = App.objects.get(package_name=event_or_action['package']['name'])
        except App.DoesNotExist:
            return None,None,None
        
        event_time = event_or_action['event_time']
        visitor, created = Visitor.objects.get_or_create(
            id=event_or_action['visitor_id'], app=app)
        logger.debug(f'    -> Visitor {visitor.id}')
        if visitor.registered_at > event_time:
            visitor.registered_at = event_time
            visitor.save()

        # that activity might have out of order, so look for a session around the actitiy time
        from_time = event_time + timedelta(hours=1)
        to_time = event_time - timedelta(hours=1)
        logger.debug(
            f'        Looking for sessions started_at <= {from_time} and ended_at >= {to_time}')
        sessions = Session.objects.filter(app=app,
            visitor=visitor, started_at__lte=from_time, ended_at__gte=to_time).order_by('-started_at')
        # session = Session.objects.filter(visitor=visitor).order_by('started_at').first()
        for session in sessions:
            logger.debug(
                f'        * {session.short_id} {session.started_at} {session.ended_at} {event_time}')
        session = None
        if len(sessions) > 0:
            session = sessions[0]

        if session is None:
            session = Session.objects.create(
                visitor=visitor,
                app=app,
                started_at=event_time,
                ended_at=event_time,
            )
        else:
            delta = event_time - session.ended_at
            if delta.total_seconds() > 3600:
                # This is a new session
                session = Session.objects.create(
                    visitor=visitor,
                    app=app,
                    started_at=event_time,
                    ended_at=event_time,
                )

        logger.debug(
            f'    -> Session {session.short_id} {session.started_at} {session.ended_at}')
        if session.started_at > event_time:
            session.started_at = event_time
        if session.ended_at < event_time:
            session.ended_at = event_time
        session.save()
        return app, visitor, session

    class Meta:
        verbose_name_plural = 'Activity'