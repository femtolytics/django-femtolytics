from django.urls import path

from femtolytics import views

app_name = 'femtolytics'
urlpatterns = [
     path('', views.index, name='index'),
     path('dashboard/<uuid:id>', views.dashboards_by_app, name='dashboards_by_app'),
     path('apps', views.apps, name='apps'),
     path('apps/add', views.apps_add, name='apps_add'),
     path('apps/edit/<uuid:id>', views.apps_edit, name='apps_edit'),
     path('apps/delete/<uuid:id>', views.apps_delete, name='apps_delete'),
     path('sessions', views.sessions, name='sessions'),
     path('sessions/<uuid:id>', views.sessions_by_app, name='sessions_by_app'),
     path('sessions/<uuid:app_id>/<uuid:session_id>', views.session, name='session'),
     path('visitors', views.visitors, name='visitors'),
     path('visitors/<uuid:id>', views.visitors_by_app, name='visitors_by_app'),
     path('visitors/<uuid:id>/<uuid:visitor_id>', views.visitor, name='visitor'),
     path('crashes', views.crashes, name='crashes'),
]
