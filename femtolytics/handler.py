import json

from dateutil import parser
from femtolytics.models import Activity

class Handler:
    @classmethod
    def on_event(cls, event, remote_ip=None, city=None):
        properties = None
        if 'properties' in event['event']:
            properties = json.dumps(event['event']['properties'])
        event['event_time'] = parser.parse(event['event']['time'])

        app, visitor, session = Activity.find_app_visitor_session(event)
        if app is None:
            return None
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
            remote_ip=remote_ip if remote_ip is not None else None,
            city=city['city'] if city is not None else None,
            region=city['region'] if city is not None and 'region' in city else None,
            country=city['country_name'] if city is not None else None,
        )
        return activity

    @classmethod
    def on_action(cls, action, remote_ip=None, city=None):
        properties = None
        if 'properties' in action['action']:
            properties = json.dumps(action['action']['properties'])
        action['event_time'] = parser.parse(action['action']['time'])

        app, visitor, session = Activity.find_app_visitor_session(action)
        if app is None:
            return None
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
            remote_ip=remote_ip if remote_ip is not None else None,
            city=city['city'] if city is not None else None,
            region=city['region'] if city is not None and 'region' in city else None,
            country=city['country_name'] if city is not None else None,
        )
        return activity
