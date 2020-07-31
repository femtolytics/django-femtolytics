import json
import uuid

from dateutil import parser
from django.conf import settings
from femtolytics.models import Activity


class Handler:
    SUCCESS = 0
    APP_NOT_FOUND = 1
    IGNORE = 2
    INVALID = 3

    @classmethod
    def log_city(cls):
        log_city = False
        if hasattr(settings, 'FEMTOLYTICS_LOG_CITY'):
            log_city = settings.FEMTOLYTICS_LOG_CITY
        return log_city

    @classmethod
    def valid_event(cls, event):
        if not Handler.valid_event_or_action(event, 'event'):
            return False
        if event['event']['type'] not in ['VIEW', 'NEW_USER', 'CRASH', 'GOAL']:
            return False
        return True

    @classmethod
    def valid_action(cls, action):
        return Handler.valid_event_or_action(event, 'action')

    @classmethod
    def valid_event_or_action(cls, event_or_action, key):
        if key not in event_or_action:
            return False
        if 'type' not in event_or_action[key] or 'time' not in event_or_action[key]:
            return False
        if not isinstance(event_or_action['event']['time'], str):
            return False
        if 'package' not in event_or_action:
            return False
        if 'name' not in event_or_action['package'] or 'version' not in event_or_action['package'] or 'build' not in event_or_action['package']:
            return False
        if 'device' not in event_or_action:
            return False
        if 'name' not in event_or_action['device'] or 'os' not in event_or_action['device']:
            return False
        if 'visitor_id' not in event_or_action:
            return False
        input_form = 'int' if isinstance(event_or_action['visitor_id'], int) else 'hex'
        try:
            return uuid.UUID(**{input_form: event_or_action['visitor_id']})
        except (AttributeError, ValueError):
            return False

        return True

    @classmethod
    def on_event(cls, event, remote_ip=None, city=None, ignore=None):
        if not Handler.valid_event(event):
            return None, Handler.INVALID

        properties = None
        if 'properties' in event['event']:
            properties = json.dumps(event['event']['properties'])
        try:
            event['event_time'] = parser.parse(event['event']['time'])
        except parser._parser.ParserError:
            return None, Handler.INVALID

        app, visitor, session = Activity.find_app_visitor_session(event)
        if app is None:
            return None, Handler.APP_NOT_FOUND
        if ignore is not None and ignore(app, visitor, session):
            return None, Handler.IGNORE
        activity = Activity.objects.create(
            visitor=visitor,
            session=session,
            app=app,
            category=Activity.EVENT,
            activity_type=event['event']['type'],
            properties=properties,
            occured_at=event['event_time'],
            device_name=event['device']['name'],
            device_os=event['device']['os'],
            package_name=event['package']['name'],
            package_version=event['package']['version'],
            package_build=event['package']['build'],
            city=city['city'] if city is not None and Handler.log_city() else None,
            region=city['region'] if city is not None and 'region' in city else None,
            country=city['country_name'] if city is not None else None,
        )
        return activity, Handler.SUCCESS

    @classmethod
    def on_action(cls, action, remote_ip=None, city=None, ignore=None):
        if not Handler.valid_action(action):
            return None, Handler.INVALID

        properties = None
        if 'properties' in action['action']:
            properties = json.dumps(action['action']['properties'])
        try:
            action['event_time'] = parser.parse(action['action']['time'])
        except parser._parser.ParserError:
            return None, Handler.INVALID

        app, visitor, session = Activity.find_app_visitor_session(action)
        if app is None:
            return None, Handler.APP_NOT_FOUND
        if ignore is not None and ignore(app, visitor, session):
            return None, Handler.IGNORE
        activity = Activity.objects.create(
            visitor=visitor,
            session=session,
            app=app,
            category=Activity.ACTION,
            activity_type=action['action']['type'],
            properties=properties,
            occured_at=action['event_time'],
            device_name=action['device']['name'],
            device_os=action['device']['os'],
            package_name=action['package']['name'],
            package_version=action['package']['version'],
            package_build=action['package']['build'],
            city=city['city'] if city is not None and Handler.log_city() else None,
            region=city['region'] if city is not None and 'region' in city else None,
            country=city['country_name'] if city is not None else None,
        )
        return activity, Handler.SUCCESS
