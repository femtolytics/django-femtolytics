from django.urls import path

from femtolytics import views
from femtolytics.api import views as api_views

app_name = 'femtolytics'
urlpatterns = [
     path('', views.DashboardView.as_view(), name='index'),
     path('dashboard/<uuid:app_id>', views.DashboardByAppView.as_view(), name='dashboards_by_app'),
     path('apps', views.AppsView.as_view(), name='apps'),
     path('apps/add', views.AppsAdd.as_view(), name='apps_add'),
     path('apps/edit/<uuid:app_id>', views.AppsEdit.as_view(), name='apps_edit'),
     path('apps/delete/<uuid:app_id>', views.AppsDelete.as_view(), name='apps_delete'),
     path('apps/activated/<uuid:app_id>', api_views.ActivatedView.as_view(), name='apps_activated'),
     path('sessions', views.SessionsView.as_view(), name='sessions'),
     path('sessions/<uuid:app_id>', views.SessionsByAppView.as_view(), name='sessions_by_app'),
     path('sessions/<uuid:app_id>/<uuid:session_id>', views.SessionView.as_view(), name='session'),
     path('visitors', views.VisitorsView.as_view(), name='visitors'),
     path('visitors/<uuid:app_id>', views.VisitorsByAppView.as_view(), name='visitors_by_app'),
     path('visitors/<uuid:app_id>/<uuid:visitor_id>', views.VisitorView.as_view(), name='visitor'),
     path('crashes/<uuid:app_id>/<uuid:crash_id>', views.CrashView.as_view(), name='crash'),
]
