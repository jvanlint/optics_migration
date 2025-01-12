import logging
import os
import time

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core import serializers
from django.core.mail import send_mail
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.templatetags.static import static
from django.urls import reverse

from ..forms import MissionFileForm, MissionForm, MissionImageryForm
from ..models import (
    Aircraft,
    Campaign,
    Comment,
    Mission,
    MissionFile,
    MissionImagery,
    Package,
    UserProfile,
)

logger = logging.getLogger(__name__)

# ---------------- Mission -------------------------


@login_required(login_url="account_login")
def mission_v2(request, link_id):
    start_time = time.time()
    logger.info(f"Retrieving mission object.[{link_id}]")

    user_profile = UserProfile.objects.get(user=request.user)
    isAdmin = user_profile.is_admin()

    try:
        mission_queryset = Mission.objects.get(id=link_id)
        mission_files_queryset = mission_queryset.missionfile_set.all()
        comments = mission_queryset.comments.all()
        packages = mission_queryset.package_set.all()
        targets = mission_queryset.target_set.all()
        threats = mission_queryset.threat_set.all()
        supports = mission_queryset.support_set.all()
        imagery = mission_queryset.missionimagery_set.all()

        breadcrumbs = {
            "Campaigns": reverse("campaigns"),
            mission_queryset.campaign.name: reverse(
                "campaign_detail_v2", args=(mission_queryset.campaign.id,)
            ),
            mission_queryset.name: "",
        }

        form = MissionFileForm(
            initial={"mission": mission_queryset, "uploaded_by": request.user.id}
        )

        end_time = time.time()
        duration = end_time - start_time
        logger.info(
            f"Retrieved mission object [{link_id} - {mission_queryset.name}] in {duration:.2f} seconds.",
            extra={
                "mission_id": mission_queryset.id,
                "mission_name": mission_queryset.name,
                "discord_msg_id": mission_queryset.discord_msg_id,
                "discord_api_id": mission_queryset.discord_api_id,
                "user": request.user,
                "isAdmin": isAdmin,
            },
        )
    except Mission.DoesNotExist:
        mission_queryset = None
        mission_files_queryset = None
        comments = None
        packages = None
        targets = None
        threats = None
        supports = None
        imagery = None
        form = None
        breadcrumbs = {"Campaigns": reverse("campaigns"), "Mission": "Not found"}
        logger.error(
            f"Mission object [{link_id}]does not exist.",
            extra={"user": user_profile.user},
        )
        # return HttpResponse(status=404)
    except Exception as e:
        logger.error(f"An error occurred: {e}", extra={"mission_id": link_id})
        return HttpResponse(status=500)

    context = {
        "mission_object": mission_queryset,
        "package_object": packages,
        "target_object": targets,
        "threat_object": threats,
        "support_object": supports,
        "imagery_object": imagery,
        "mission_files": mission_files_queryset,
        "isAdmin": isAdmin,
        "comments": comments,
        "file_form": form,
        "breadcrumbs": breadcrumbs,
    }

    return render(request, "v2/mission/mission.html", context=context)


@login_required(login_url="account_login")
def mission_add_v2(request, link_id):
    campaign = Campaign.objects.get(id=link_id)
    missionCount = campaign.mission_set.count() + 1
    returnURL = request.GET.get("returnUrl")
    image_url = (
        request.build_absolute_uri(campaign.campaignImage.url)
        if campaign.campaignImage
        else request.build_absolute_uri(static("assets/no_image.png"))
    )

    form_title = "Mission"

    form = MissionForm(
        initial={
            "campaign": campaign,
            "number": missionCount,
            "creator": request.user.id,
        }
    )

    if request.method == "POST":
        form = MissionForm(request.POST, request.FILES)
        if form.is_valid():
            tmp = form.save(commit=False)
            tmp.created_by = request.user
            tmp.modified_by = request.user
            tmp.save()
            if tmp.notify_discord:
                tmp.create_discord_event(image_url, request)
            return HttpResponseRedirect(returnURL)

    context = {
        "form": form,
        "form_title": form_title,
        "link": link_id,
        "returnURL": returnURL,
    }
    return render(request, "v2/generic/data_entry_form.html", context=context)


@login_required(login_url="account_login")
def mission_update_v2(request, link_id):
    mission = Mission.objects.get(id=link_id)
    returnURL = request.GET.get("returnUrl")

    image_url = request.build_absolute_uri(mission.campaign.campaignImage.url)

    # mission.create_discord_event(image_url, request)

    form_title = "Mission"

    form = MissionForm(instance=mission)

    if request.method == "POST":
        form = MissionForm(request.POST, request.FILES, instance=mission)

        if form.is_valid():
            saved_obj = form.save(commit=False)
            saved_obj.modified_by = request.user
            saved_obj.save()

            if saved_obj.notify_discord:
                saved_obj.create_discord_event(image_url, request)
            return HttpResponseRedirect(returnURL)

    context = {
        "form": form,
        "form_title": form_title,
        "link": link_id,
        "returnURL": returnURL,
    }
    return render(request, "v2/generic/data_entry_form.html", context=context)


@login_required(login_url="account_login")
def mission_delete_v2(request, link_id):
    mission = Mission.objects.get(id=link_id)
    returnURL = request.GET.get("returnUrl")

    mission_files = mission.missionfile_set.all()

    # Check to see if an AO Image exists.
    if mission_files:
        for file in mission_files:
            file.delete()

    if mission.discord_msg_id:
        mission.delete_discord_event()
    mission.delete()

    return HttpResponseRedirect(returnURL)


@login_required(login_url="account_login")
def mission_copy_v2(request, link_id):
    mission = Mission.objects.get(id=link_id)
    # Send the user to the copy function so we know who created the mission.
    campaignID = mission.copy(request.user)

    returnURL = request.GET.get("returnUrl")

    return HttpResponseRedirect(returnURL)


# ---------------- Mission Comments -------------------------
@login_required(login_url="account_login")
def mission_add_comment(request):
    # if this is a POST request we need to process the form data
    mission_id = request.GET.get("mission_id")

    if request.method == "POST":
        comment_data = request.POST.dict()
        comment = comment_data.get("comment_text")
        # Get the post object
        mission_object = Mission.objects.get(pk=mission_id)
        mission_object.comments.create(comment=comment, user=request.user)

    context = mission_all_comments(mission_id)

    return render(request, "v2/mission/includes/comments.html", context=context)


@login_required(login_url="account_login")
def mission_delete_comment(request, link_id):
    comment = Comment.objects.get(id=link_id)
    mission_id = request.GET.get("mission_id")

    comment.delete()

    context = mission_all_comments(mission_id)

    return render(request, "v2/mission/includes/comments.html", context=context)


def mission_edit_comment(request, link_id):
    comment = Comment.objects.get(id=link_id)

    mission_id = request.GET.get("mission_id")
    mission = Mission.objects.get(id=mission_id)

    context = {
        "comment": comment,
        "mission_object": mission,
    }

    return render(request, "v2/mission/includes/comment_edit.html", context=context)


def mission_show_comments(request):
    mission_id = request.GET.get("mission_id")
    context = mission_all_comments(mission_id)

    return render(request, "v2/mission/includes/comments.html", context=context)


def mission_update_comment(request, link_id):
    comment = Comment.objects.get(id=link_id)
    mission_id = request.GET.get("mission_id")

    if request.method == "POST":
        comment_data = request.POST.dict()
        comment_text = comment_data.get("comment_edit_text")
        comment.comment = comment_text
        comment.save()

    context = mission_all_comments(mission_id)

    return render(request, "v2/mission/includes/comments.html", context=context)


def mission_all_comments(mission_id):
    mission = Mission.objects.get(id=mission_id)
    comments = mission.comments.all()

    context = {
        "comments": comments,
        "mission_object": mission,
    }

    return context


# ---------------- Mission File -------------------------


@login_required(login_url="account_login")
def mission_file_add(request):
    # if this is a POST request we need to process the form data
    returnURL = request.GET.get("returnUrl")
    print("landed")
    form = MissionFileForm(request.POST, request.FILES)

    if form.is_valid():
        print("form valid")
        form.save(commit=True)
        return HttpResponseRedirect(returnURL)
        print("success00")

    print("fail")
    return HttpResponseRedirect(returnURL)


@login_required(login_url="account_login")
def mission_file_delete(request, link_id):
    mission_file_obj = MissionFile.objects.get(id=link_id)
    returnURL = request.GET.get("returnUrl")

    # Check to see if an AO Image exists.
    if mission_file_obj:
        mission_file_obj.delete()

    return HttpResponseRedirect(returnURL)


# ---------------- Mission Imagery -------------------------


@login_required(login_url="account_login")
def mission_imagery_create_v2(request, link_id):
    mission = Mission.objects.get(id=link_id)
    returnURL = request.GET.get("returnUrl")

    form = MissionImageryForm(initial={"mission": mission})
    form_title = "Mission Image"

    if request.method == "POST":
        form = MissionImageryForm(request.POST, request.FILES)
        if form.is_valid():
            form.save(commit=True)
            return HttpResponseRedirect(returnURL)

    context = {
        "form": form,
        "form_title": form_title,
        "link": link_id,
        "returnURL": returnURL,
    }
    return render(request, "v2/generic/data_entry_form.html", context=context)


@login_required(login_url="account_login")
def mission_imagery_update_v2(request, link_id):
    imagery = MissionImagery.objects.get(id=link_id)
    returnURL = request.GET.get("returnUrl")

    form_title = "Mission Image"
    form = MissionImageryForm(instance=imagery)

    if request.method == "POST":
        form = MissionImageryForm(request.POST, request.FILES, instance=imagery)
        print(request.path)
        if form.is_valid():
            form.save(commit=True)
            return HttpResponseRedirect(returnURL)

    context = {
        "form": form,
        "form_title": form_title,
        "link": link_id,
        "returnURL": returnURL,
    }
    return render(request, "v2/generic/data_entry_form.html", context=context)


@login_required(login_url="account_login")
def mission_imagery_delete_v2(request, link_id):
    imagery = MissionImagery.objects.get(id=link_id)
    returnURL = request.GET.get("returnUrl")

    # Check to see if an AO Image exists.
    if imagery:
        imagery.delete()

    return HttpResponseRedirect(returnURL)


# ---------------- Mission Signup -------------------------


@login_required(login_url="account_login")
def mission_signup_v2(request, link_id):  # link_id is the mission ID
    logger.info(f"{request.user} has launched signup for [{link_id}]")

    mission = Mission.objects.get(id=link_id)
    comments = mission.comments.all()
    packages = mission.package_set.all()

    has_seat = 0
    package_list = serializers.serialize("python", packages)
    for package in package_list:
        has_seat += (
            Aircraft.objects.filter(flight__package__id=package["pk"])
            .filter(pilot=request.user)
            .count()
        )
        has_seat += (
            Aircraft.objects.filter(flight__package__id=package["pk"])
            .filter(rio_wso=request.user)
            .count()
        )
    campaign = Campaign.objects.get(mission=mission)
    is_owner = campaign.created_by == request.user

    breadcrumbs = {
        "Campaigns": reverse("campaigns"),
        mission.campaign.name: reverse(
            "campaign_detail_v2", args=(mission.campaign.id,)
        ),
        mission.name: reverse("mission_v2", args=(mission.id,)),
        "Sign Up": "",
    }

    context = {
        "mission_object": mission,
        "package_object": packages,
        "has_seat": has_seat,
        "is_owner": is_owner,
        "comments": comments,
        "breadcrumbs": breadcrumbs,
    }

    return render(request, "v2/mission/mission_signup.html", context)


# Flagged for deletion
# @login_required(login_url="account_login")
# def mission_signup(request, link_id):  # link_id is the mission ID
#     mission = Mission.objects.get(id=link_id)
#     packages = mission.package_set.all()

#     has_seat = 0
#     package_list = serializers.serialize("python", packages)
#     for package in package_list:
#         has_seat += (
#             Aircraft.objects.filter(flight__package__id=package["pk"])
#             .filter(pilot=request.user)
#             .count()
#         )
#         has_seat += (
#             Aircraft.objects.filter(flight__package__id=package["pk"])
#             .filter(rio_wso=request.user)
#             .count()
#         )
#     campaign = Campaign.objects.get(mission=mission)
#     is_owner = campaign.created_by == request.user
#     context = {
#         "mission_object": mission,
#         "package_object": packages,
#         "has_seat": has_seat,
#         "is_owner": is_owner,
#     }

#     return render(request, "mission/mission_signup.html", context)


@login_required(login_url="account_login")
def mission_signup_update(request, link_id, seat_id):

    returnURL = request.GET.get("returnUrl")
    aircraft = Aircraft.objects.get(pk=link_id)
    if seat_id == 1:
        aircraft.pilot = request.user
    else:
        aircraft.rio_wso = request.user

    aircraft.save()

    logger.info(
        f"{request.user} has signed up for [{aircraft.type.name}] in mission [{aircraft.flight.package.mission.name}]"
    )

    return HttpResponseRedirect(returnURL)


@login_required(login_url="account_login")
def mission_signup_remove(request, link_id, seat_id):
    returnURL = request.GET.get("returnUrl")
    aircraft = Aircraft.objects.get(pk=link_id)
    if seat_id == 1:
        aircraft.pilot = None
    else:
        aircraft.rio_wso = None

    aircraft.save()

    return HttpResponseRedirect(returnURL)
