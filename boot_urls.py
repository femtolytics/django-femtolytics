from django.urls import path, include

urlpatterns = [
    path('', include('femtolytics.urls')),
    path('api/v1/', include('femtolytics.api.urls')),
]