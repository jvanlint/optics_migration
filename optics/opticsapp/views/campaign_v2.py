# For deleting physical files (like images) when campaign is deleted.
import logging
import os
import time

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse, reverse_lazy

from ..forms import CampaignForm
from ..models import Campaign, Comment, UserProfile

logger = logging.getLogger(__name__)


@login_required(login_url="account_login")
def campaigns_all(request):
    """
    Retrieves all campaign objects and returns a HTML file displaying all objects.

    Args:
            request: The Django request object.

    Returns:
            A rendered HTML page with context containing campaign data, whether the user is an admin and breadcrumbs.
    """

    campaigns_queryset = Campaign.objects.filter(
        status__name__iexact="Active"
    ).order_by("status", "name")

    logger.info("Retrieved all campaigns.")

    user_profile = UserProfile.objects.get(user=request.user)

    breadcrumbs = {"Home": ""}

    context = {
        "campaigns": campaigns_queryset,
        "isAdmin": user_profile.is_admin(),
        "breadcrumbs": breadcrumbs,
    }

    return render(request, "v2/campaign/campaigns.html", context=context)


@login_required(login_url="account_login")
def campaigns_filter(request):
    filter = request.GET.get("filter")

    if filter == "All":
        campaigns_queryset = Campaign.objects.order_by("status", "name")
    else:
        campaigns_queryset = Campaign.objects.filter(
            status__name__iexact=filter
        ).order_by("status", "name")

    user_profile = UserProfile.objects.get(user=request.user)

    breadcrumbs = {"Home": ""}

    logger.info(
        "Filtered campaigns by: " + filter,
        extra={"retrieved_campaigns": str(campaigns_queryset)},
    )

    context = {
        "campaigns": campaigns_queryset,
        "isAdmin": user_profile.is_admin(),
        "breadcrumbs": breadcrumbs,
    }

    return render(request, "v2/campaign/includes/campaign_card.html", context=context)


@login_required(login_url="account_login")
def campaign_detail_v2(request, link_id):
    start_time = time.time()
    logger.info(f"Retrieving campaign object.[{link_id}]")

    user_profile = UserProfile.objects.get(user=request.user)
    isAdmin = user_profile.is_admin()

    try:
        campaign = Campaign.objects.get(id=link_id)
        missions = campaign.mission_set.all().order_by("number")
        comments = campaign.comments.all()
        breadcrumbs = {"Campaigns": reverse_lazy("campaigns"), campaign.name: ""}
        campaign.refresh_from_db()

        end_time = time.time()
        duration = end_time - start_time
        logger.info(
            f"Retrieved campaign object [{link_id} - {campaign.name}] in {duration:.2f} seconds.",
            extra={
                "campaign_id": link_id,
                "campaign_name": campaign.name,
                "user": request.user,
                "isAdmin": isAdmin,
            },
        )
    except Campaign.DoesNotExist:
        campaign = None
        missions = None
        comments = None
        breadcrumbs = {"Campaigns": reverse_lazy("campaigns")}
        logger.error(
            f"Campaign object [{link_id}] does not exist.",
            extra={"user": user_profile.user},
        )
    except Exception as e:
        logger.error(f"An error occurred: {e}", extra={"campaign_id": link_id})
        return HttpResponse(status=500)

    context = {
        "campaign_object": campaign,
        "mission_object": missions,
        "isAdmin": isAdmin,
        "comments": comments,
        "breadcrumbs": breadcrumbs,
    }

    return render(request, "v2/campaign/campaign.html", context=context)


@login_required(login_url="account_login")
def campaign_add_v2(request):

    breadcrumbs = {"Campaigns": reverse("home"), "Add": ""}

    if request.method == "POST":
        form = CampaignForm(request.POST, request.FILES)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.modified_by = request.user
            obj.created_by = request.user
            obj.save()
            campaign_name = form.cleaned_data.get("name")

            logger.info(
                "Campaign added.",
                extra={"campaign name": campaign_name, "user": request.user},
            )
            # messages.success(request, "Campaign successfully created.")
            return HttpResponseRedirect(reverse_lazy("campaigns"))
    else:
        form = CampaignForm(initial={"creator": request.user.id})

    context = {
        "form": form,
        "action": "Add",
        "breadcrumbs": breadcrumbs,
    }

    # Render the HTML template index.html with the data in the context variable
    return render(request, "v2/campaign/campaign_form.html", context)


@login_required(login_url="account_login")
def campaign_update_v2(request, link_id):
    campaign = Campaign.objects.get(id=link_id)
    form = CampaignForm(instance=campaign)
    return_url = request.GET.get("returnUrl")
    breadcrumbs = {
        "Campaigns": reverse_lazy("campaigns"),
        campaign.name: reverse_lazy("campaign_detail_v2", args=(campaign.id,)),
        "Edit": "",
    }

    if request.method == "POST":
        form = CampaignForm(request.POST, request.FILES, instance=campaign)
        print(request.path)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.modified_by = request.user
            obj.save()

            campaign_name = form.cleaned_data.get("name")

            logger.info(
                "Campaign updated.",
                extra={"campaign name": campaign_name, "user": request.user},
            )

            # messages.success(request, "Campaign successfully updated.")
            return HttpResponseRedirect(return_url)

    context = {
        "form": form,
        "link": link_id,
        "returnURL": return_url,
        "breadcrumbs": breadcrumbs,
        "action": "Edit",
    }
    return render(request, "v2/campaign/campaign_form.html", context=context)


@login_required(login_url="account_login")
def campaign_delete_v2(request, link_id):
    campaign = Campaign.objects.get(id=link_id)
    campaign_name = campaign.name

    campaign.delete()

    logger.info(
        "Campaign deleted.",
        extra={"campaign_name": campaign_name, "user": request.user},
    )
    # messages.success(request, "Campaign successfully deleted.")
    campaigns_queryset = Campaign.objects.order_by("status", "name")
    user_profile = UserProfile.objects.get(user=request.user)

    context = {
        "campaigns": campaigns_queryset,
        "isAdmin": user_profile.is_admin(),
    }

    return render(request, "v2/campaign/includes/campaign_card.html", context=context)


# ---------------- Campaign Comments -------------------------
def campaign_add_comment(request):

    campaign_id = request.GET.get("campaign_id")

    if request.method == "POST":
        comment_data = request.POST.dict()
        comment = comment_data.get("comment_text")
        # Get the post object
        campaign = Campaign.objects.get(pk=campaign_id)
        campaign.comments.create(comment=comment, user=request.user)

        logger.info(
            "Campaign comment added.",
            extra={
                "campaign_name": campaign.name,
                "comment": comment,
                "user": request.user,
            },
        )

    context = campaign_all_comments(campaign_id)

    return render(request, "v2/campaign/includes/comments.html", context=context)


def campaign_delete_comment(request, link_id):

    campaign_id = request.GET.get("campaign_id")
    comment = Comment.objects.get(id=link_id)

    logger.info(
        "Campaign comment deleted.", extra={"comment": comment, "user": request.user}
    )

    comment.delete()

    context = campaign_all_comments(campaign_id)

    return render(request, "v2/campaign/includes/comments.html", context=context)


def campaign_edit_comment(request, link_id):
    comment = Comment.objects.get(id=link_id)

    campaign_id = request.GET.get("campaign_id")
    campaign = Campaign.objects.get(id=campaign_id)

    logger.info(
        "Campaign comment edited.", extra={"comment": comment, "user": request.user}
    )

    context = {
        "comment": comment,
        "campaign_object": campaign,
    }

    return render(request, "v2/campaign/includes/comment_edit.html", context=context)


def campaign_show_comments(request):
    campaign_id = request.GET.get("campaign_id")
    context = campaign_all_comments(campaign_id)

    return render(request, "v2/campaign/includes/comments.html", context=context)


def campaign_update_comment(request, link_id):
    comment = Comment.objects.get(id=link_id)
    campaign_id = request.GET.get("campaign_id")

    if request.method == "POST":
        comment_data = request.POST.dict()
        comment_text = comment_data.get("comment_edit_text")
        comment.comment = comment_text
        comment.save()

    context = campaign_all_comments(campaign_id)

    return render(request, "v2/campaign/includes/comments.html", context=context)


def campaign_all_comments(campaign_id):

    campaign = Campaign.objects.get(id=campaign_id)
    comments = campaign.comments.all()

    context = {
        "comments": comments,
        "campaign_object": campaign,
    }

    return context


# **** End Campaigns Code *****
