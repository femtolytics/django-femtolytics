# django-femtolytics
 
This is the open-source code used for [femtolytics.com](https://femtolytics.com). With this django package you can run your own instance of femtolytics and not depend on any third-party tracking for understanding how people use your mobile application.

You can find a Flutter client for femtolytics at [https://pub.dev/packages/femtolytics](https://pub.dev/packages/femtolytics)

You can find a Django sample project that is configured properly to run django-femtolytics at [django-femtolytics-sample](https://github.com/femtolytics/django-femtolytics-sample). If you already have an existing Django project and want to incorporate django-femtolytics into it, follow the instructions below.

## Getting Started

First you will need to install the dependency
```
pip install django-femtolytics
```

Or add it to your requirements.txt
```
django-femtolytics
```

### Setting up

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
    path('analytics/api/v1/', include('femtolytics.api.urls')),
    path('analytics/', include('femtolytics.urls')),
]
```

The `femtolytics.api.urls` corresponds to the endpoint that the mobile application client will send information to. You should make sure it matches the URL you pass when configuring the client in your application.

The `femtolytics.urls` are the main dashboard URLs which will give you access to insights on what your users are doing. You will be able to track, sessions, visitors, custom actions, goals and crashes.

Finally make sure to install the migrations
```
python manage.py migrate
```

All of the dashboard URLS `femtolytics.urls` will require a user to be logged in, so you can make sure nobody has access to that information.

### Tracking

Femtolytics requires to have created an application with the same package name you used in your application. So make sure to visit the dashboard and `add an application` before generating event in your client.

## Customizing

The dashboard is customizable as it uses `Template Views` and `Form Views`.

Here are the different views that are used

- `DashboardView` is a springboard view which will select the first registered mobile application and redirect to the dashboard of that view.
- `DashboardByAppView` to generate the dashboard for a particular application.
- `AppsView` shows the list of configured applications.
- `AppsAdd` is a FormView to add register a new application.
- `AppsEdit` is the same FormView but to edit an existing application.
- `AppsDelete` to delete an application.
- `SessionsView` is a springboard view which will select the first registered mobile application and redirect to the list of sessions for that application.
- `SessionsByAppView` shows the list of sessions for a particular application.
- `SessionView` shows a particular session.
- `VisitorsView` is a sprinboard view which will select the first registered mobile application and redirect to the list of visitors for that application.
- `VisitorsByAppView` shows the list of visitors for a particular application.
- `VisitorView` shows a particular visitor.
- `CrashesView` is a sprinboard view which will select the first registered mobile application and redirect to the list of crashes for that application.
- `CrashesByAppView` shows a list of crashes for a particular application.
- `CrashView` shows a particular crash.
- `GoalsView` is a sprinboard view which will select the first registered mobile application and redirect to the list of goals for that application.
- `GoalsByAppView` shows a list of goals for a particular application.
- `GoalView` shows a particular goal.

The springboard views `DashboardView`, `SessionsView`, `VisitorsView`, `CrashesView` and `GoalsView` take a `success_url` and `failed_url` for the redirects. If an application is found it redirects to `success_url` otherwise redirects to `failed_url`.

Only `AppsAdd`, `AppsEdit` and `AppsDelete` take a `success_url` parameter to define where to redirect after adding, editing or deleting an application.

Here is a sample custom routing definition to use your custom templates:
```python
app_name = "analytics"
urlpatterns = [
    path("", views.index, name="index"),
    # Dashboard
    path(
        "dashboard",
        subscription_required()(
            femto_views.DashboardView.as_view(
                success_url="analytics:dashboards_by_app",
                failed_url="analytics:apps_add",
            )
        ),
        name="dashboard",
    ),
    path(
        "dashboard/<uuid:app_id>",
        subscription_required()(
            femto_views.DashboardByAppView.as_view(
                template_name="analytics/dashboard.html",
            )
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
        "sessions",
        subscription_required()(
            femto_views.SessionsView.as_view(
                success_url="analytics:sessions_by_app",
                failed_url="analytics:account",
            ),
        ),
        name="sessions",
    ),
    path(
        "sessions/<uuid:app_id>",
        subscription_required()(
            femto_views.SessionsByAppView.as_view(
                template_name="analytics/sessions.html",
            )
        ),
        name="sessions_by_app",
    ),
    path(
        "sessions/<uuid:app_id>/<uuid:session_id>",
        subscription_required()(
            femto_views.SessionView.as_view(
                template_name="analytics/session.html",
            )
        ),
        name="session",
    ),
    # Visitors
    path(
        "visitors",
        subscription_required()(
            femto_views.VisitorsView.as_view(
                success_url="analytics:visitors_by_app",
                failed_url="analytics:account",
            )
        ),
        name="visitors",
    ),
    path(
        "visitors/<uuid:app_id>",
        subscription_required()(
            femto_views.VisitorsByAppView.as_view(
                template_name="analytics/visitors.html",
            )
        ),
        name="visitors_by_app",
    ),
    path(
        "visitors/<uuid:app_id>/<uuid:visitor_id>",
        subscription_required()(
            femto_views.VisitorView.as_view(
                template_name="analytics/visitor.html",
            )
        ),
        name="visitor",
    ),
    # Crash
    path(
        "crashes/<uuid:app_id>/<uuid:crash_id>",
        subscription_required()(
            femto_views.CrashView.as_view(
                template_name="analytics/crash.html",
            )
        ),
        name="crash",
    ),
    # Goal
    path(
        "goals/<uuid:app_id>/<uuid:goal_id>",
        subscription_required()(
            femto_views.GoalView.as_view(
                template_name="analytics/goal.html",
            )
        ),
        name="goal",
    ),
]
```

