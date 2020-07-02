import json
import logging

from datetime import datetime, timedelta
from dateutil import parser
from django.contrib.auth.decorators import login_required

from django.db.models.functions import TruncDay
from django.db.models import Count
from django.shortcuts import render, redirect, get_object_or_404, Http404
from femtolytics.models import App, Session, Visitor, Activity
from femtolytics.forms import AppForm
from rest_framework import authentication, permissions, serializers, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

logger = logging.getLogger("femtolytics")


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


@login_required
def index(request):
    apps = App.objects.filter(owner=request.user)
    if apps.count() == 0:
        return redirect('femtolytics:apps')
    else:
        return redirect('femtolytics:dashboards_by_app', apps[0].id)


@login_required
def dashboards_by_app(request, id):
    app = get_object_or_404(App, pk=id)
    if app.owner != request.user:
        return Http404

    context = {}
    context['apps'] = App.objects.filter(owner=request.user)
    context['app'] = app
    context['sessions'] = Session.objects.filter(app=app).order_by('-ended_at')[:5]

    # Graph information (Last 30 days for now)
    thirty = datetime.now() - timedelta(days=30)
    stats = {}
    sessions = Session.objects.filter(app=app, started_at__gte=thirty).annotate(day=TruncDay(
        'started_at')).values('day').annotate(c=Count('id')).values('day', 'c')
    for session in sessions:
        stats[session['day']] = {
            'sessions': session['c'],
            'visitors': 0,
        }
    visitors = Visitor.objects.filter(app=app, registered_at__gte=thirty).annotate(day=TruncDay(
        'registered_at')).values('day').annotate(c=Count('id')).values('day', 'c')
    for visitor in visitors:
        if visitor['day'] not in stats:
            stats[visitor['day']] = {
                'sessions': 0,
                'visitors': 0,
            }
        stats[visitor['day']]['visitors'] = visitor['c']
    entries = []
    for day in sorted(stats):
        entries.append({
            'day': day,
            'sessions': stats[day]['sessions'],
            'visitors': stats[day]['visitors'],
        })
    context['stats'] = entries

    # Map Information
    try:
        import pycountry

        activities = Activity.objects.filter(app=app, occured_at__gte=thirty).values('country').annotate(c=Count('visitor_id', distinct=True)).values('country', 'c')
        locations = []
        min_sessions = 0
        max_sessions = None
        for activity in activities:
            if min_sessions is None or activity['c'] < min_sessions:
                min_sessions = activity['c']
            if max_sessions is None or activity['c'] > max_sessions:
                max_sessions = activity['c']

            locations.append({
                'country': activity['country'],
                'alpha_2': pycountry.countries.get(name=activity['country']).alpha_2,
                'alpha_3': pycountry.countries.get(name=activity['country']).alpha_3,
                'count': activity['c'],
            })
        for location in locations:
            if max_sessions > min_sessions:
                r = (location['count'] - min_sessions) / (max_sessions - min_sessions)
                r = round(r, 1)
                location['fill'] = 'FILL{}'.format(r)
            else:
                location['fill'] = 'FILL0.7'
            
        context['locations'] = locations
    except ImportError as e:
        pass

    return render(request, 'femtolytics/dashboard.html', context)


@login_required
def visitor(request, id, visitor_id):
    visitor = get_object_or_404(Visitor, pk=visitor_id)
    if visitor.app.owner != request.user:
        return Http404

    context = {}
    context['visitor'] = visitor
    context['sessions'] = Session.objects.filter(
        visitor=visitor_id).order_by('-ended_at')
    return render(request, 'femtolytics/visitor.html', context)


@login_required
def apps(request):
    context = {}
    context['apps'] = App.objects.filter(owner=request.user)
    return render(request, 'femtolytics/apps.html', context)


@login_required
def apps_add(request):
    if request.method == 'POST':
        form = AppForm(request.POST)
        if form.is_valid():
            app = form.save(commit=False)
            app.owner = request.user
            app.save()
            return redirect('femtolytics:apps')
    context = {}
    context['form'] = AppForm()
    return render(request, 'femtolytics/apps_add.html', context)


@login_required
def apps_edit(request, id):
    app = get_object_or_404(App, pk=id)
    if request.method == 'POST':
        form = AppForm(request.POST, instance=app)
        if form.is_valid():
            app = form.save()
            return redirect('femtolytics:apps')     

    context = {}
    context['app'] = app
    context['form'] = AppForm()
    return render(request, 'femtolytics/apps_add.html', context)

@login_required
def apps_delete(request, id):
    app = get_object_or_404(App, pk=id)
    if app.owner != request.user:
        raise Http404
    app.delete()
    return redirect('femtolytics:apps')

@login_required
def sessions(request):
    apps = App.objects.filter(owner=request.user)
    if apps.count() == 0:
        return redirect('femtolytics:apps')
    
    return redirect('femtolytics:sessions_by_app', apps[0].id)

@login_required
def sessions_by_app(request, id):
    app = get_object_or_404(App, pk=id)
    if app.owner != request.user:
        raise Http404

    context = {}
    context['app'] = app
    context['apps'] = App.objects.filter(owner=request.user)
    context['sessions'] = Session.objects.filter(app=app).order_by('-ended_at')
    return render(request, 'femtolytics/sessions.html', context)

@login_required
def session(request, app_id, session_id):
    app = get_object_or_404(App, pk=app_id)
    if app.owner != request.user:
        raise Http404
    session = get_object_or_404(Session, pk=session_id)
    if session.app != app:
        raise Http404
    context = {}
    context['session'] = session
    return render(request, 'femtolytics/session.html', context)

@login_required
def visitors(request):
    apps = App.objects.filter(owner=request.user)
    if apps.count() == 0:
        return redirect('femtolytics:apps')
    
    return redirect('femtolytics:visitors_by_app', apps[0].id)

@login_required
def visitors_by_app(request, id):
    app = get_object_or_404(App, pk=id)
    if app.owner != request.user:
        raise Http404

    context = {}
    context['app'] = app
    context['apps'] = App.objects.filter(owner=request.user)
    context['visitors'] = Visitor.objects.filter(app=app).order_by('registered_at')
    return render(request, 'femtolytics/visitors.html', context)

@login_required
def crashes(request):
    pass


@api_view(['POST'])
@permission_classes((permissions.AllowAny,))
def on_event(request):
    body_unicode = request.body.decode('utf-8')
    body = json.loads(body_unicode)

    event = body['events'][0]
    logger.info('{} {}'.format(event['device']
                               ['name'], event['event']['type']))
    remote_ip, city = get_geo_info(request)
    
    for event in body['events']:
        properties = None
        if 'properties' in event['event']:
            properties = json.dumps(event['event']['properties'])
        event['event_time'] = parser.parse(event['event']['time'])

        app, visitor, session = Activity.find_app_visitor_session(event)
        if app is None:
            raise Http404
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

    return Response({'status': 'ok'})


@api_view(['POST'])
@permission_classes((permissions.AllowAny,))
def on_action(request):
    body_unicode = request.body.decode('utf-8')
    body = json.loads(body_unicode)
    action = body['actions'][0]
    logger.info('{} {}'.format(
        action['device']['name'], action['action']['type']))
    remote_ip, city = get_geo_info(request)
    
    for action in body['actions']:
        properties = None
        if 'properties' in action['action']:
            properties = json.dumps(action['action']['properties'])
        action['event_time'] = parser.parse(action['action']['time'])

        app, visitor, session = Activity.find_app_visitor_session(action)
        if app is None:
            raise Http404
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

    return Response({'status': 'ok'})
