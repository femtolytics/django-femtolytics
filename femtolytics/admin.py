from femtolytics.models import App, Session, Visitor, Activity
from django.contrib import admin

@admin.register(Activity)
class ActivityAdmin(admin.ModelAdmin):
    ordering = ['-occured_at']
    list_display = ['short_id', 'user', 'sid', 'activity_type', 'properties', 'version', 'device_os', 'occured_at']
    list_filter = ['visitor', 'activity_type']
    date_hierarchy = 'occured_at'

    def sid(self, obj):
        return obj.session.short_id
    sid.short_description = 'Session'

    def user(self, obj):
        return obj.visitor.short_id
    user.short_description = 'User'

    def version(self, obj):
        return f"{obj.package_version}.{obj.package_build}"

@admin.register(Session)
class SessionAdmin(admin.ModelAdmin):
    ordering = ['-started_at']
    list_display = ['short_id', 'user', 'started_at', 'ended_at']
    date_hierarchy = 'started_at'

    def user(self, obj):
        return obj.visitor.short_id
    user.short_description = 'User'

@admin.register(Visitor)
class VisitorAdmin(admin.ModelAdmin):
    ordering = ['-created_at']
    list_display = ['short_id', 'created_at']
    date_hierarchy = 'created_at'
