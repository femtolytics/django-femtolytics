from django.urls import path
from rest_framework.urlpatterns import format_suffix_patterns

from femtolytics.api import views

app_name = 'femtolytics_api'
urlpatterns = [
     path('event', views.EventView.as_view(), name='event'),
     path('action', views.ActionView.as_view(), name='action'),
]
urlpatterns = format_suffix_patterns(urlpatterns)
