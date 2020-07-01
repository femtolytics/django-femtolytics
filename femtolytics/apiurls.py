from django.urls import path
from rest_framework.urlpatterns import format_suffix_patterns

from femtolytics import views

app_name = 'femtolytics_api'
urlpatterns = [
     path('event', views.on_event, name='event'),
     path('action', views.on_action, name='action'),
]
urlpatterns = format_suffix_patterns(urlpatterns)
