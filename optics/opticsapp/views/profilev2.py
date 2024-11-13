import os
from collections import namedtuple

import boto3
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.shortcuts import redirect, render
from django.urls import reverse

from optics.opticsapp.forms import ProfileForm
from optics.opticsapp.models import Comment, UserProfile


@login_required(login_url="account_login")
def own_profile_view(request):
    comments = Comment.objects.filter(user=request.user)
    profile_form = ProfileForm(instance=request.user.profile)
    breadcrumbs = {"Campaigns": reverse("campaigns"), "Own Profile": ""}
    context = {
        "comments": comments,
        "breadcrumbs": breadcrumbs,
        "profile_form": profile_form,
    }
    if request.method == "POST":
        profile_form = ProfileForm(request.POST, instance=request.user.profile)
        if profile_form.is_valid():
            profile_form.save()
            messages.success(request, "Your profile was successfully updated!")
            return redirect("own_profile")
        else:
            messages.error(request, "Please correct the error below.")
    return render(request, "v2/profile/profile.html", context=context)


@login_required(login_url="account_login")
def select_avatar(request):
    context = {}
    new_file = []

    if settings.DEBUG:
        files = os.listdir(os.path.join(settings.MEDIA_ROOT, "assets/img/avatars/"))
        for file in files:
            new_file.append(f"assets/img/avatars/{file}")
    else:
        s3 = boto3.resource("s3")
        bucket = s3.Bucket(settings.AWS_STORAGE_BUCKET_NAME)
        files = [
            obj.key
            for obj in bucket.objects.filter(Prefix="static/assets/img/avatars/")
        ]

        for file in files:
            # We need to take out the static/ part of the file path to make the URI in S3 resolve correctly.
            new_file.append(file.replace("static/", ""))

    files = new_file
    context = {"files": files}
    return render(request, "v2/profile/avatar_selection.html", context=context)


@login_required(login_url="account_login")
def change_avatar(request):
    avatar_image = request.GET.get("avatar")
    profile = UserProfile.objects.get(user=request.user)
    profile.profile_image = avatar_image
    profile.save()

    comments = Comment.objects.filter(user=request.user)

    context = {"comments": comments}

    return render(request, "v2/profile/avatar_selection.html", context=context)


@login_required(login_url="account_login")
def user_profile_view(request, link_id):

    user_profile = User.objects.get(pk=link_id)
    breadcrumbs = {"Campaigns": reverse("campaigns"), "User Profile": ""}

    comments = Comment.objects.filter(user=user_profile)

    context = {
        "profile_object": user_profile,
        "comments": comments,
        "breadcrumbs": breadcrumbs,
    }
    return render(request, "v2/profile/user_profile.html", context=context)
