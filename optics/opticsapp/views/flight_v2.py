import os
from django.conf import settings
from django.shortcuts import render

from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_GET

from django.http import HttpResponse, HttpResponseRedirect, JsonResponse

from django.urls import reverse

from ..models import (
    Flight,
    FlightImagery,
    UserProfile,
    Comment,
    Package,
    Target,
    Aircraft,
    Airframe,
    AirframeDefaults,
)
from ..forms import FlightForm, FlightImageryForm


@login_required(login_url="account_login")
def flight_v2(request, link_id):
    flight = Flight.objects.get(id=link_id)
    aircraft = flight.aircraft_set.all()
    waypoints = flight.waypoint_set.all().order_by("number")
    targets = flight.targets.all()
    comments = flight.comments.all()
    imagery = flight.flightimagery_set.all()
    user_profile = UserProfile.objects.get(user=request.user)

    breadcrumbs = {
        "Home": reverse("campaigns"),
        flight.package.mission.campaign.name: reverse(
            "campaign_detail_v2", args=(flight.package.mission.campaign.id,)
        ),
        flight.package.mission.name: reverse(
            "mission_v2", args=(flight.package.mission.id,)
        ),
        flight.package.name: reverse("package_v2", args=(flight.package.id,)),
        flight.callsign: "",
    }

    context = {
        "flight_object": flight,
        "aircraft_object": aircraft,
        "waypoint_object": waypoints,
        "target_object": targets,
        "imagery_object": imagery,
        "isAdmin": user_profile.is_admin(),
        "comments": comments,
        "breadcrumbs": breadcrumbs,
    }

    return render(request, "v2/flight/flight.html", context=context)


@login_required(login_url="account_login")
def flight_add_v2(request, link_id):
    package = Package.objects.get(id=link_id)

    # Filter the target field to just targets from the mission.
    target = Target.objects.filter(mission=package.mission.id)

    returnURL = request.GET.get("returnUrl")

    form_title = "Flight"
    form = FlightForm(target, initial={"package": package})

    context = {
        "form": form,
        "form_title": form_title,
        "link": link_id,
        "returnURL": returnURL,
    }

    if request.method == "POST":
        print(f'Flight post data: {request.POST}')
        post_form = FlightForm(target, request.POST)
        if post_form.is_valid():
            obj = post_form.save(commit=False)
            obj.modified_by = request.user
            obj.created_by = request.user
            print(f"Object id is: {obj.id}")
            flight_id = obj.id
            airframe_id = obj.airframe.id
            obj.save()
            print(f"Object id is: {obj.id}")
            flight_id = obj.id
            create_flight_aircraft(flight_id, airframe_id)
            # TODO: When a flight is created some default values for radios and callsigns should be populated.
            # TODO: The flight form should also enable the selection of the callsign associated with the airframe.
            obj.callsign = post_form.cleaned_data["callsign"]
            obj.save()
            obj.targets.set(post_form.cleaned_data['targets'])
            obj.save()
            # populate_airframe_defaults(flight_id, airframe_id)
            return HttpResponseRedirect(returnURL)
        else:
            print(form.errors)
            print(request.POST)

    return render(request, "v2/generic/data_entry_form.html", context=context)


@login_required(login_url="account_login")
def flight_update_v2(request, link_id):
    flight = Flight.objects.get(id=link_id)
    returnURL = request.GET.get("returnUrl")

    form_title = "Flight"

    # Filter the target field to just targets from the mission.
    target = Target.objects.filter(mission=flight.package.mission.id)

    form = FlightForm(target, instance=flight)

    if request.method == "POST":
        form = FlightForm(target, request.POST, instance=flight)
        print(request.path)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.modified_by = request.user
            # TODO: When airframe type is updated the aircraft should be updated.
            obj.save()
            obj.targets.set(form.cleaned_data['targets'])
            obj.save()
            return HttpResponseRedirect(returnURL)

    context = {
        "form": form,
        "form_title": form_title,
        "link": link_id,
        "returnURL": returnURL,
    }
    return render(request, "v2/generic/data_entry_form.html", context=context)


@login_required(login_url="account_login")
def flight_delete_v2(request, link_id):
    flight = Flight.objects.get(id=link_id)
    returnURL = request.GET.get("returnUrl")

    flight.delete()

    return HttpResponseRedirect(returnURL)


@login_required(login_url="account_login")
def flight_copy_v2(request, link_id):
    flight = Flight.objects.get(id=link_id)
    returnURL = request.GET.get("returnUrl")
    packageID = flight.copy(request.user)

    return HttpResponseRedirect(returnURL)


# Candidate for removal.
@login_required(login_url="account_login")
def flight_copy(request, link_id):
    flight = Flight.objects.get(id=link_id)
    packageID = flight.copy()

    return HttpResponseRedirect("/airops/package/" + str(packageID))


# ---------------- Flight Comments -------------------------
@login_required(login_url="account_login")
def flight_add_comment(request):
    # if this is a POST request we need to process the form data
    flight_id = request.GET.get("flight_id")

    if request.method == "POST":
        comment_data = request.POST.dict()
        comment = comment_data.get("comment_text")
        # Get the post object
        flight_object = Flight.objects.get(pk=flight_id)
        flight_object.comments.create(comment=comment, user=request.user)

    context = flight_all_comments(flight_id)

    return render(request, "v2/flight/includes/comments.html", context=context)


@login_required(login_url="account_login")
def flight_delete_comment(request, link_id):
    flight_id = request.GET.get("flight_id")
    comment = Comment.objects.get(id=link_id)

    comment.delete()

    context = flight_all_comments(flight_id)

    return render(request, "v2/flight/includes/comments.html", context=context)


def flight_edit_comment(request, link_id):
    comment = Comment.objects.get(id=link_id)

    flight_id = request.GET.get("flight_id")
    flight = Flight.objects.get(id=flight_id)

    context = {
        "comment": comment,
        "flight_object": flight,
    }

    return render(request, "v2/flight/includes/comment_edit.html", context=context)


def flight_show_comments(request):
    flight_id = request.GET.get("flight_id")
    context = flight_all_comments(flight_id)

    return render(request, "v2/flight/includes/comments.html", context=context)


def flight_update_comment(request, link_id):
    comment = Comment.objects.get(id=link_id)
    flight_id = request.GET.get("flight_id")

    if request.method == "POST":
        comment_data = request.POST.dict()
        comment_text = comment_data.get("comment_edit_text")
        comment.comment = comment_text
        comment.save()

    context = flight_all_comments(flight_id)

    return render(request, "v2/flight/includes/comments.html", context=context)


def flight_all_comments(flight_id):
    flight = Flight.objects.get(id=flight_id)
    comments = flight.comments.all()

    context = {
        "comments": comments,
        "flight_object": flight,
    }

    return context


# ---------------- Flight Imagery -------------------------


@login_required(login_url="account_login")
def flight_imagery_create_v2(request, link_id):
    flight = Flight.objects.get(id=link_id)
    returnURL = request.GET.get("returnUrl")

    form = FlightImageryForm(initial={"flight": flight})
    form_title = "Flight Image"

    if request.method == "POST":
        form = FlightImageryForm(request.POST, request.FILES)
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
def flight_imagery_update_v2(request, link_id):
    imagery = FlightImagery.objects.get(id=link_id)
    returnURL = request.GET.get("returnUrl")

    form_title = "Flight Image"
    form = FlightImageryForm(instance=imagery)

    if request.method == "POST":
        form = FlightImageryForm(request.POST, request.FILES, instance=imagery)
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
def flight_imagery_delete_v2(request, link_id):
    imagery = FlightImagery.objects.get(id=link_id)
    returnURL = request.GET.get("returnUrl")

    # Check to see if an AO Image exists.
    if imagery:
        imagery.delete()

    
    return HttpResponseRedirect(returnURL)


def create_flight_aircraft(flight_id, airframe_id):
    airframe = Airframe.objects.get(id=airframe_id)
    flight = Flight.objects.get(id=flight_id)

    for _ in range(2):
        new_aircraft = Aircraft(type=airframe, flight=flight)
        new_aircraft.save()


# Not sure that is even needed
def populate_airframe_defaults(flight_id, airframe_id):
    # airframe = Airframe.objects.get(id=airframe_id)
    airframe_defaults = AirframeDefaults.objects.get(airframe_type=airframe_id)
    flight = Flight.objects.get(id=flight_id)
    flight.callsign = airframe_defaults.callsign
    flight.radio_frequency = airframe_defaults.default_radio_freq
    flight.flight_coordination = airframe_defaults.laser_code
    flight.save()


@require_GET
def get_callsigns(request, airframe_id):
    airframe_defaults = AirframeDefaults.objects.filter(airframe_type=airframe_id)
    callsigns = [ad.callsign for ad in airframe_defaults]
    return JsonResponse(callsigns, safe=False)
