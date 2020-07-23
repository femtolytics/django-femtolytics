import logging
import json 

from femtolytics.handler import Handler
from rest_framework import authentication, permissions, serializers, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView

logger = logging.getLogger("femtolytics")

class EventView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request, format=None):
        body_unicode = request.body.decode('utf-8')
        body = json.loads(body_unicode)

        event = body['events'][0]
        logger.info('{} {}'.format(event['device']
                                ['name'], event['event']['type']))
        remote_ip, city = get_geo_info(request)

        for event in body['events']:
            activity = Handler.on_event(event, remote_ip=remote_ip, city=city)
            if activity is None:
                raise Http404

        return Response({'status': 'ok'})


class ActionView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request, format=None):
        body_unicode = request.body.decode('utf-8')
        body = json.loads(body_unicode)
        action = body['actions'][0]
        logger.info('{} {}'.format(
            action['device']['name'], action['action']['type']))
        remote_ip, city = get_geo_info(request)

        for action in body['actions']:
            activity = Handler.on_action(action, remote_ip=remote_ip, city=city)
            if activity is None:
                raise Http404

        return Response({'status': 'ok'})


def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def get_geo_info(request):
    try:
        from django.contrib.gis.geoip2 import GeoIP2
    except ImportError as e:
        return None, None

    g = GeoIP2()
    remote_ip = None
    city = None
    try:
        remote_ip = get_client_ip(request)
        city = g.city(remote_ip)
    except:
        return None, None
    return remote_ip, city

