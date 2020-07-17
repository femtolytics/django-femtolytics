# django-femtolytics
 
This is the open-source code used for [femtolytics.com](https://femtolytics.com). With this django package you can run your own instance of femtolytics and not depend on any third-party tracking for understanding how people use your mobile application.

You can find a Flutter client for femtolytics at [https://pub.dev/packages/femtolytics](https://pub.dev/packages/femtolytics)

## Getting Started

First you will need to install the dependency
```
pip install django-femtolytics
```

Or add it to your requirements.txt
```
django-femtolytics
```

## Setting up

In your project's settings.py add femtolytics to the list of applications

```python
INSTALLED_APPS = [
    ...
    'femtolytics',
]
```

Then, you can add the path to your project URLs:

```python
from django.conf import settings
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('analytics/20200515/', include('femtolytics.apiurls')),
    path('analytics/', include('femtolytics.urls')),
]
```

The `femtolytics.apiurls` corresponds to the endpoint that the mobile application client will send information to. You shold make sure it matches the URL you pass when configuring the client in your application.

The `femtolytics.urls` are the main dashboard which will give you access to insights on what your users are doing. You will be able to track, sessions, visitors, custom actions and goals as well as crashes.

Finally make sure to install the migrations
```
python manage.py migrate
```

All of the dashboard URLS `femtolytics.urls` will require a user to be logged in, so you can make sure nobody has access to that information.

## Tracking

Femtolytics requires to have created an application with the same package name you used in your application. So make sure to visit the dashboard and `add an application` before generating event in your client.

## Customizing

The dashboard is customizable as it uses `Template Views` and `Form Views`.

Here are the different views that are used

- `DashboardByAppView` to generate the dashboard for a particular application.
- `AppsView` shows the list of configured applications.
- `AppsAdd` is a FormView to add register a new application.
- `AppsEdit` is the same FormView but to edit an existing application.
- `AppsDelete` to delete an application.
- `SessionsByAppView` shows the list of sessions for a particular application.
- `SessionView` shows a particular session.
- `VisitorsByAppView` shows the list of visitors for a particular application.
- `VisitorView` shows a particular visitor.

Only `AppsAdd`, `AppsEdit` and `AppsDelete` take a `success_url` parameter to define where to redirect after adding, editing or deleting an application.

Here is a sample custom routing definition to use your custom templates:
```python
app_name = "analytics"
urlpatterns = [
    path("", views.index, name="index"),
    # Dashboard
    path(
        "dashboard/<uuid:app_id>",
        femto_views.DashboardByAppView.as_view(
            template_name="analytics/dashboard.html",
        ),
        name="dashboards_by_app",
    ),
    # Apps
    path(
        "apps/",
        femto_views.AppsView.as_view(template_name="analytics/apps.html",),
        name="apps",
    ),
    path(
        "apps/add",
        femto_views.AppsAdd.as_view(
            template_name="analytics/apps_add.html",
            success_url=reverse_lazy("analytics:apps"),
        ),
        name="apps_add",
    ),
    path(
        "apps/edit/<uuid:app_id>",
        femto_views.AppsEdit.as_view(
            template_name="analytics/apps_add.html",
            success_url=reverse_lazy("analytics:apps"),
        ),
        name="apps_edit",
    ),
    path(
        "apps/delete/<uuid:app_id>",
        femto_views.AppsDelete.as_view(success_url=reverse_lazy("analytics:apps"),),
        name="apps_delete",
    ),
    # Sessions
    path(
        "sessions/<uuid:app_id>",
        femto_views.SessionsByAppView.as_view(
            template_name="analytics/sessions.html",
        ),
        name="sessions_by_app",
    ),
    path(
        "sessions/<uuid:app_id>/<uuid:session_id>",
        femto_views.SessionView.as_view(template_name="analytics/session.html",)
        name="session",
    ),
    # Visitors
    path(
        "visitors/<uuid:app_id>",
        femto_views.VisitorsByAppView.as_view(
            template_name="analytics/visitors.html",
        )
        name="visitors_by_app",
    ),
    path(
        "visitors/<uuid:app_id>/<uuid:visitor_id>",
        femto_views.VisitorView.as_view(template_name="analytics/visitor.html",)
        name="visitor",
    ),
]

```

