from django.contrib import admin
from import_export.admin import ImportExportModelAdmin
from django.utils.html import format_html
from django.templatetags.static import static

# Register your models here.

from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin

from .models import (
    Campaign,
    Mission,
    Package,
    Flight,
    Aircraft,
    Status,
    Airframe,
    Terrain,
    Threat,
    Target,
    WebHook,
    MissionFile,
    Support,
    Waypoint,
    Task,
    MissionImagery,
    ThreatReference,
    Squadron,
    UserProfile,
    AirframeDefaults,
)

# Define the admin class

admin.site.site_url = "/"


class CampaignAdmin(admin.ModelAdmin):
    list_display = ("name", "start_date", "status", "date_created")
    list_filter = ("start_date", "status")


# Register the admin class with the associated model
admin.site.register(Campaign, CampaignAdmin)


class PackageInline(admin.TabularInline):
    model = Package
    extra = 3


class MissionAdmin(admin.ModelAdmin):
    list_display = ("number", "name", "mission_date", "get_campaign")
    inlines = [PackageInline]

    def get_campaign(self, obj):
        return obj.campaign.name

    get_campaign.short_description = "Campaign"


admin.site.register(Mission, MissionAdmin)


class FlightInline(admin.TabularInline):
    model = Flight
    extra = 3


class PackageAdmin(admin.ModelAdmin):
    list_display = ("name", "get_mission", "get_campaign")
    inlines = [FlightInline]

    def get_mission(self, obj):
        return obj.mission.name

    get_mission.short_description = "Mission"

    def get_campaign(self, obj):
        return obj.mission.campaign.name

    get_campaign.short_description = "Campaign"


admin.site.register(Package, PackageAdmin)


class FlightAdmin(admin.ModelAdmin):
    list_display = ("callsign", "get_package", "get_mission", "get_campaign")

    def get_package(self, obj):
        return obj.package.name

    get_package.short_description = "Package"

    def get_mission(self, obj):
        return obj.package.mission.name

    get_mission.short_description = "Mission"

    def get_campaign(self, obj):
        return obj.package.mission.campaign.name

    get_campaign.short_description = "Campaign"


admin.site.register(Flight, FlightAdmin)


class AircraftAdmin(admin.ModelAdmin):
    list_display = ("type", "get_flight")

    def get_flight(self, obj):
        return obj.flight.callsign

    get_flight.short_description = "Flight"


admin.site.register(Aircraft, AircraftAdmin)


class StatusAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = ("name",)


admin.site.register(Status, StatusAdmin)


class TerrainAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = ("name",)


admin.site.register(Terrain, TerrainAdmin)


class AirframeAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = ("name",)


admin.site.register(Airframe, AirframeAdmin)


class AirframeDefaultsAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = ("airframe_type", "callsign", "default_radio_freq", "laser_code")


admin.site.register(AirframeDefaults, AirframeDefaultsAdmin)


class ThreatAdmin(admin.ModelAdmin):
    list_display = ("name",)


admin.site.register(Threat, ThreatAdmin)


class TaskAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = ("name",)


admin.site.register(Task, TaskAdmin)


class TargetAdmin(admin.ModelAdmin):
    list_display = ("name",)


admin.site.register(Target, TargetAdmin)


class SupportAdmin(admin.ModelAdmin):
    list_display = ("callsign",)


admin.site.register(Support, SupportAdmin)


class WaypointAdmin(admin.ModelAdmin):
    list_display = ("name",)


admin.site.register(Waypoint, WaypointAdmin)


class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = "UserInfo"


class UserProfileAdmin(admin.ModelAdmin):
    def group(self, user):
        groups = []
        for group in user.groups.all():
            groups.append(group.name)
        return " ".join(groups)

    group.short_description = "Groups"
    inlines = [
        UserProfileInline,
    ]
    list_display = [
        "username",
        "first_name",
        "last_name",
        "is_active",
        "email",
        "group",
    ]
    ordering = ["username"]


admin.site.unregister(User)
admin.site.register(User, UserProfileAdmin)


class ThreatReferenceAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = ("name", "nato_code", "threat_class", "threat_type", "harm_code")


admin.site.register(ThreatReference, ThreatReferenceAdmin)


class MissionImageryAdmin(admin.ModelAdmin):
    list_display = ("mission", "caption", "image")

    def image_tag(self, obj):
        url = static(obj.image)
        return format_html('<img src="{}" width="50" height="50" />', url)


admin.site.register(MissionImagery, MissionImageryAdmin)


class MissionFileAdmin(admin.ModelAdmin):
    list_display = (
        "mission",
        "name",
        "mission_file",
    )


admin.site.register(MissionFile, MissionFileAdmin)


class WebHookAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = (
        "service_name",
        "url",
    )
    ordering = ["-service_name"]


admin.site.register(WebHook, WebHookAdmin)


class UserProfileAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = (
        "user",
        "squadron",
        "profile_image",
        "timezone",
    )


admin.site.register(UserProfile, UserProfileAdmin)


class SquadronAdmin(admin.ModelAdmin):
    list_display = ("squadron_name", "squadron_url")


admin.site.register(Squadron, SquadronAdmin)
