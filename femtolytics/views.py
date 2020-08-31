import json
import logging

from datetime import timedelta
from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models.functions import TruncDay
from django.db.models import Count
from django.shortcuts import render, redirect, get_object_or_404, Http404
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.views.generic.base import View, TemplateView
from femtolytics.models import Activity, App, Crash, Goal, Session, Visitor
from femtolytics.forms import AppForm

logger = logging.getLogger("femtolytics")


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
        
        # Do we have any data?
        context['activated'] = Session.objects.filter(app=app).count() > 0
        
        # Last 5 sessions
        context['sessions'] = Session.objects.filter(
            app=app).prefetch_related('visitor').order_by('-ended_at')[:5]

        # Graph information (for the last `duration` days)
        duration = int(request.GET.get('duration', 30))
        context['duration'] = duration
        period_start = timezone.now() - timedelta(days=duration)
        stats = {}
        # Create empty entries
        tzinfo = None
        for index in range(0, duration):
            then = period_start + timedelta(days=index)
            then = timezone.datetime(then.year, then.month, then.day, tzinfo=then.tzinfo)
            tzinfo = then.tzinfo
            stats[then] = {
                'sessions': 0,
                'visitors': 0,
            }
        # SELECT COUNT(*) AS c, DATE(started_at) AS day FROM sessions GROUP BY day
        sessions = Session.objects.filter(app=app, started_at__gte=period_start).annotate(day=TruncDay(
            'started_at')).values('day').annotate(c=Count('id')).values('day', 'c')
        context['session_count'] = 0
        for session in sessions:
            then = timezone.datetime(session['day'].year, session['day'].month, session['day'].day, tzinfo=tzinfo)
            stats[then] = {
                'sessions': session['c'],
                'visitors': 0,
            }
            context['session_count'] += session['c']
        # SELECT COUNT(*) AS c, DATE(registered_at) AS day FROM visitors GROUP BY day
        visitors = Visitor.objects.filter(app=app, registered_at__gte=period_start).annotate(day=TruncDay(
            'registered_at')).values('day').annotate(c=Count('id')).values('day', 'c')
        context['visitor_count'] = 0
        for visitor in visitors:
            then = timezone.datetime(visitor['day'].year, visitor['day'].month, visitor['day'].day, tzinfo=tzinfo)
            stats[then]['visitors'] = visitor['c']
            context['visitor_count'] += visitor['c']
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
                    country = pycountry.countries.get(name=activity['country'])
                    locations.append({
                        'country': activity['country'],
                        'alpha_2': country.alpha_2 if country is not None else None,
                        'alpha_3': country.alpha_3 if country is not None else None,
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

        # Goals
        goals = Goal.objects.filter(app=app, last_at__gte=period_start).prefetch_related('activities')
        goal_map = {}
        for goal in goals:
            goal_map[goal.name] = {
                'id': goal.id,
                'short_id': goal.short_id,
                'count': goal.activities.count(),
            }
        context['goals'] = goal_map

        # Crashes
        crashes = Crash.objects.filter(app=app, last_at__gte=period_start).prefetch_related('activities')
        crash_map = {}
        for crash in crashes:
            crash_map[crash.signature] = {
                'id': crash.id,
                'short_id': crash.short_id,
                'count': crash.activities.count(),
                'sample': crash.activities.first().analyzed_properties,
            }
        context['crashes'] = crash_map

        # Compute 30-DAU
        thirty = timezone.now() - timedelta(days=30)
        min_sessions = 2
        if hasattr(settings, 'FEMTOLYTICS_30DAU_SESSIONS_THRESHOLD'):
            min_sessions = settings.FEMTOLYTICS_30DAU_SESSIONS_THRESHOLD

        activities = Activity.objects.filter(app=app, occured_at__gte=thirty).values(
            'visitor_id').annotate(c=Count('session_id', distinct=True)).filter(c__gte=min_sessions).values('visitor_id', 'c')
        context['30dau'] = activities.count()

        # Compute 7-DAU
        seven = timezone.now() - timedelta(days=7)
        min_sessions = 2
        if hasattr(settings, 'FEMTOLYTICS_7DAU_SESSIONS_THRESHOLD'):
            min_sessions = settings.FEMTOLYTICS_7DAU_SESSIONS_THRESHOLD

        activities = Activity.objects.filter(app=app, occured_at__gte=seven).values(
            'visitor_id').annotate(c=Count('session_id', distinct=True)).filter(c__gte=min_sessions).values('visitor_id', 'c')
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
            visitor=visitor_id).prefetch_related('visitor', 'app').order_by('-ended_at')
        return render(request, self.template_name, context)


class AppsView(View, LoginRequiredMixin):
    template_name = 'femtolytics/apps.html'

    def get(self, request):
        context = {}
        context['apps'] = App.objects.filter(owner=request.user)
        return render(request, self.template_name, context)


class AppsAdd(View, LoginRequiredMixin):
    template_name = 'femtolytics/apps_add.html'
    success_url = reverse_lazy('femtolytics:apps_instructions')

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
            url = self.success_url
            if isinstance(url, str):
                url = reverse(url, kwargs={'app_id': app.id})
            return redirect(url, app.id)
        else:
            context = {}
            context['form'] = form
            return render(request, self.template_name, context)


class AppsInstructions(View, LoginRequiredMixin):
    template_name = 'femtolytics/apps_instructions.html'

    def get(self, request, app_id):
        app = get_object_or_404(App, pk=app_id)
        context = {}
        context['app'] = app
        return render(request, self.template_name, context)


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
        context['sessions'] = Session.objects.filter(app=app).prefetch_related('visitor', 'app', 'activity_set').order_by('-ended_at')
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
            app=app).order_by('-registered_at')
        return render(request, self.template_name, context)

class CrashView(View, LoginRequiredMixin):
    template_name = 'femtolytics/crash.html'

    def get(self, request, app_id, crash_id):
        app = get_object_or_404(App, pk=app_id)
        if app.owner != request.user:
            raise Http404
        crash = get_object_or_404(Crash, pk=crash_id)
        if crash.app != app:
            raise Http404
    
        context = {}
        context['app'] = app
        context['crash'] = crash
        return render(request, self.template_name, context)

class GoalView(View, LoginRequiredMixin):
    template_name = 'femtolytics/goal.html'

    def get(self, request, app_id, goal_id):
        app = get_object_or_404(App, pk=app_id)
        if app.owner != request.user:
            raise Http404
        goal = get_object_or_404(Goal, pk=goal_id)
        if goal.app != app:
            raise Http404
    
        context = {}
        context['app'] = app
        context['goal'] = goal
        return render(request, self.template_name, context)
