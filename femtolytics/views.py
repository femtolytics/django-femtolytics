import json
import logging
import pytz

from datetime import datetime, timedelta
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models.functions import TruncDay
from django.db.models import Count
from django.shortcuts import render, redirect, get_object_or_404, Http404
from django.urls import reverse_lazy
from django.views.generic.base import View, TemplateView
from femtolytics.models import App, Session, Visitor, Activity
from femtolytics.forms import AppForm
from femtolytics.handler import Handler
from rest_framework import authentication, permissions, serializers, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

utc = pytz.UTC

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


class DashboardView(View, LoginRequiredMixin):
    success_url = 'femtolytics:dashboards_by_app'
    failed_url = 'femtolytics:apps'
    
    def get(self, request):
        apps = App.objects.filter(owner=request.user)
        if apps.count() == 0:
            return redirect(self.failed_url)
        else:
            return redirect(self.success_url, apps[0].id)
    

class DashboardByAppView(View, LoginRequiredMixin):
    template_name = 'femtolytics/dashboard.html'

    def get(self, request, app_id):
        app = get_object_or_404(App, pk=app_id)
        if app.owner != request.user:
            return Http404

        context = {}
        context['apps'] = App.objects.filter(owner=request.user)
        context['app'] = app
        
        # Last 5 sessions
        context['sessions'] = Session.objects.filter(
            app=app).order_by('-ended_at')[:5]

        # Graph information (Last `duration` days for now)
        duration = int(request.GET.get('duration', 30))
        period_start = datetime.now() - timedelta(days=duration)
        stats = {}
        # Create empty entries 
        for index in range(0, duration):
            then = period_start + timedelta(days=index)
            then = datetime(then.year, then.month, then.day)
            stats[then.replace(tzinfo=utc)] = {
                'sessions': 0,
                'visitors': 0,
            }
        # SELECT COUNT(*) AS c, DATE(started_at) AS day FROM sessions GROUP BY day
        sessions = Session.objects.filter(app=app, started_at__gte=period_start).annotate(day=TruncDay(
            'started_at')).values('day').annotate(c=Count('id')).values('day', 'c')
        for session in sessions:
            stats[session['day'].replace(tzinfo=utc)] = {
                'sessions': session['c'],
                'visitors': 0,
            }
        context['session_count'] = sessions.count()
        # SELECT COUNT(*) AS c, DATE(registered_at) AS day FROM visitors GROUP BY day
        visitors = Visitor.objects.filter(app=app, registered_at__gte=period_start).annotate(day=TruncDay(
            'registered_at')).values('day').annotate(c=Count('id')).values('day', 'c')
        for visitor in visitors:
            if visitor['day'].replace(tzinfo=utc) not in stats:
                stats[visitor['day'].replace(tzinfo=utc)] = {
                    'sessions': 0,
                    'visitors': 0,
                }
            stats[visitor['day'].replace(tzinfo=utc)]['visitors'] = visitor['c']
        context['visitor_count'] = visitors.count()
        # Organize entries to be easily graphed.
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
            # SELECT COUNT(DISTINCT(visitor_id)) AS c, country FROM activity GROUP BY country
            activities = Activity.objects.filter(app=app, occured_at__gte=period_start).values(
                'country').annotate(c=Count('visitor_id', distinct=True)).values('country', 'c')
            locations = []
            min_sessions = 0
            max_sessions = None
            for activity in activities:
                if activity['country'] is not None:
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
                    r = (location['count'] - min_sessions) / \
                        (max_sessions - min_sessions)
                    r = round(r, 1)
                    location['fill'] = 'FILL{}'.format(r)
                else:
                    location['fill'] = 'FILL0.7'

            context['locations'] = locations
        except ImportError as e:
            # pycountry unavailable, ignore silently
            pass

        # Compute 30-DAU
        thirty = datetime.now() - timedelta(days=30)
        min_sessions = 2
        if hasattr(settings, 'FEMTOLYTICS_30DAU_SESSIONS_THRESHOLD'):
            min_sessions = settings.FEMTOLYTICS_30DAU_SESSIONS_THRESHOLD

        activities = Activity.objects.filter(app=app, occured_at__gte=thirty).values(
            'visitor_id').annotate(c=Count('session_id', distinct=True)).filter(c__gt=2).values('visitor_id', 'c')
        context['30dau'] = activities.count()

        # Compute 7-DAU
        seven = datetime.now() - timedelta(days=7)
        min_sessions = 2
        if hasattr(settings, 'FEMTOLYTICS_7DAU_SESSIONS_THRESHOLD'):
            min_sessions = settings.FEMTOLYTICS_7DAU_SESSIONS_THRESHOLD

        activities = Activity.objects.filter(app=app, occured_at__gte=seven).values(
            'visitor_id').annotate(c=Count('session_id', distinct=True)).filter(c__gt=2).values('visitor_id', 'c')
        context['7dau'] = activities.count()

        return render(request, self.template_name, context)


class VisitorView(View, LoginRequiredMixin):
    template_name = 'femtolytics/visitor.html'

    def get(self, request, app_id, visitor_id):
        visitor = get_object_or_404(Visitor, pk=visitor_id)
        if visitor.app.owner != request.user:
            return Http404

        context = {}
        context['visitor'] = visitor
        context['sessions'] = Session.objects.filter(
            visitor=visitor_id).order_by('-ended_at')
        return render(request, self.template_name, context)


class AppsView(View, LoginRequiredMixin):
    template_name = 'femtolytics/apps.html'

    def get(self, request):
        context = {}
        context['apps'] = App.objects.filter(owner=request.user)
        return render(request, self.template_name, context)


class AppsAdd(View, LoginRequiredMixin):
    template_name = 'femtolytics/apps_add.html'
    success_url = reverse_lazy('femtolytics:apps')

    def get(self, request):
        context = {}
        context['form'] = AppForm()
        return render(request, self.template_name, context)
    
    def post(self, request):
        form = AppForm(request.POST)
        if form.is_valid():
            app = form.save(commit=False)
            app.owner = request.user
            app.save()
            return redirect(self.success_url)

class AppsEdit(View, LoginRequiredMixin):
    template_name = 'femtolytics/apps_add.html'
    success_url = reverse_lazy('femtolytics:apps')
    
    def get(self, request, app_id):
        app = get_object_or_404(App, pk=app_id)
        context = {}
        context['app'] = app
        context['form'] = AppForm(instance=app)
        return render(request, self.template_name, context)
    
    def post(self, request, app_id):
        app = get_object_or_404(App, pk=app_id)
        form = AppForm(request.POST, instance=app)
        if form.is_valid():
            app = form.save()
            return redirect(self.success_url)

class AppsDelete(View, LoginRequiredMixin):
    success_url = reverse_lazy('femtolytics:apps')

    def get(self, request, app_id):
        app = get_object_or_404(App, pk=app_id)
        if app.owner != request.user:
            raise Http404
        app.delete()
        return redirect(self.success_url)


class SessionsView(View, LoginRequiredMixin):
    success_url = 'femtolytics:sessions_by_app'
    failed_url = 'femtolytics:apps'
    
    def get(self, request):
        apps = App.objects.filter(owner=request.user)
        if apps.count() == 0:
            return redirect(self.failed_url)

        return redirect(self.success_url, apps[0].id)

class SessionsByAppView(View, LoginRequiredMixin):
    template_name = 'femtolytics/sessions.html'

    def get(self, request, app_id):
        app = get_object_or_404(App, pk=app_id)
        if app.owner != request.user:
            raise Http404

        context = {}
        context['app'] = app
        context['apps'] = App.objects.filter(owner=request.user)
        context['sessions'] = Session.objects.filter(app=app).order_by('-ended_at')
        return render(request, self.template_name, context)

class SessionView(View, LoginRequiredMixin):
    template_name = 'femtolytics/session.html'

    def get(self, request, app_id, session_id):
        app = get_object_or_404(App, pk=app_id)
        if app.owner != request.user:
            raise Http404
        session = get_object_or_404(Session, pk=session_id)
        if session.app != app:
            raise Http404
        context = {}
        context['session'] = session
        return render(request, self.template_name, context)


class VisitorsView(View, LoginRequiredMixin):
    success_url = 'femtolytics:visitors_by_app'
    failed_url = 'femtolytics:apps'

    def get(self, request):
        apps = App.objects.filter(owner=request.user)
        if apps.count() == 0:
            return redirect(self.failed_url)

        return redirect(self.success_url, apps[0].id)

class VisitorsByAppView(View, LoginRequiredMixin):
    template_name = 'femtolytics/visitors.html'

    def get(self, request, app_id):
        app = get_object_or_404(App, pk=app_id)
        if app.owner != request.user:
            raise Http404

        context = {}
        context['app'] = app
        context['apps'] = App.objects.filter(owner=request.user)
        context['visitors'] = Visitor.objects.filter(
            app=app).order_by('registered_at')
        return render(request, self.template_name, context)


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
        activity = Handler.on_event(event, remote_ip=remote_ip, city=city)
        if activity is None:
            raise Http404

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
        activity = Handler.on_action(action, remote_ip=remote_ip, city=city)
        if activity is None:
            raise Http404

    return Response({'status': 'ok'})
