import logging
import json 

from django.http import HttpResponse, Http404
from django.shortcuts import get_object_or_404
from femtolytics.handler import Handler
from femtolytics.models import App, Session
from rest_framework import authentication, permissions, serializers, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView

logger = logging.getLogger("femtolytics")

class ActivatedView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, app_id, format=None):
        app = get_object_or_404(App, pk=app_id)
        return Response({
            'activated': Session.objects.filter(app=app).count() > 0,
        })

class EventView(APIView):
    permission_classes = [permissions.AllowAny]

    def ignore(self, app, visitor, session):
        return False

    def post(self, request, format=None):
        body_unicode = request.body.decode('utf-8')
        try:
            body = json.loads(body_unicode)
        except json.decoder.JSONDecodeError:
            return HttpResponse(status=400)

        if 'events' not in body:
            return HttpResponse(status=400)
        if len(body['events']) == 0:
            return Response({'status': 'ok'})

        event = body['events'][0]
        if not Handler.valid_event(event):
            return HttpResponse(status=400)
        logger.info('{} {}'.format(event['device']
                                ['name'], event['event']['type']))
        remote_ip, city = get_geo_info(request)

        callback=lambda app, visitor, session: self.ignore(app, visitor, session)

        for event in body['events']:
            activity, result = Handler.on_event(event, remote_ip=remote_ip, city=city, ignore=callback)
            if activity is None:
                if result == Handler.INVALID:
                    return HttpResponse(status=400)
                elif result == Handler.IGNORE:
                    return HttpResponse(status=402)
                else:
                    raise Http404

        return Response({'status': 'ok'})


class ActionView(APIView):
    permission_classes = [permissions.AllowAny]

    def ignore(self, app, visitor, session):
        return False

    def post(self, request, format=None):
        body_unicode = request.body.decode('utf-8')
        try:
            body = json.loads(body_unicode)
        except json.decoder.JSONDecodeError:
            return HttpResponse(status=400)

        if 'actions' not in body:
            return HttpResponse(status=400)
        if len(body['actions']) == 0:
            return Response({'status': 'ok'})

        action = body['actions'][0]
        if not Handler.valid_action(action):
            return HttpResponse(status=400)

        logger.info('{} {}'.format(
            action['device']['name'], action['action']['type']))
        remote_ip, city = get_geo_info(request)
        
        callback=lambda app, visitor, session: self.ignore(app, visitor, session)
        
        for action in body['actions']:
            activity, result = Handler.on_action(action, remote_ip=remote_ip, city=city, ignore=callback)
            if activity is None:
                if result == Handler.INVALID:
                    return HttpResponse(status=400)
                elif result == Handler.IGNORE:
                    return HttpResponse(status=402)
                else:
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

