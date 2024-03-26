from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.shortcuts import redirect
from django.utils import timezone
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

from django.urls import reverse

from ..models import (
    ThreatReference,
)
from ..forms import (
    ThreatReferenceForm,
)


@login_required(login_url="login")
def threat_reference_table(request):
    threat_reference = ThreatReference.objects.order_by("name")

    page_num = request.GET.get("page", 1)
    threat_reference_paginated = Paginator(
        object_list=threat_reference, per_page=15
    ).get_page(page_num)

    breadcrumbs = {"Home": reverse("index"), "Threat Reference": ""}

    template = "v2/threatdb/threat_database.html"
    context = {
        "threat_object": threat_reference_paginated,
        "breadcrumbs": breadcrumbs,
    }

    return render(request, template_name=template, context=context)


def threat_page_manager(request):
    threat = ThreatReference.objects.order_by("name")
    page_num = request.GET.get("page", 1)
    threat_paginated = Paginator(object_list=threat, per_page=15).get_page(page_num)

    template = "v2/threatdb/threats.html"
    context = {"threat_object": threat_paginated}

    return render(request, template_name=template, context=context)


def threat_object_add(request):
    breadcrumbs = {
        "Home": reverse("home"),
        "Threat Reference": reverse("threat_db"),
        "Add": "",
    }
    returnURL = request.GET.get("returnUrl")

    if request.method == "POST":
        formobj = ThreatReferenceForm
        form = formobj(request.POST, request.FILES)
        if form.is_valid():
            obj = form.save(commit=False)
            # obj.date_modified = timezone.now()
            # obj.user = request.user
            obj.save()
            return redirect("threat_db")
    else:
        form = ThreatReferenceForm

    context = {
        "form": form,
        "returnURL": returnURL,
        "action": "Add",
        "breadcrumbs": breadcrumbs,
    }

    # Render the HTML template index.html with the data in the context variable
    return render(request, "v2/generic/data_entry_form.html", context)


def threat_object_update(request):
    obj = ThreatReference.objects.get(id=link_id)
    form = ThreatReferenceForm(instance=obj)
    returnURL = request.GET.get("returnUrl")
    breadcrumbs = {
        "Home": reverse("home"),
        "Threat Reference": reverse("threat_db"),
        "Edit": "",
    }

    if request.method == "POST":
        form = formobj(request.POST, instance=obj)
        if form.is_valid():
            form_obj = form.save(commit=False)
            form_obj.date_modified = timezone.now()
            form_obj.user = request.user
            form_obj.save()
            # messages.success(request, "Campaign successfully created.")
            return redirect("reference_tables")

    context = {
        "form": form,
        "action": "Edit",
        "returnURL": returnURL,
        "breadcrumbs": breadcrumbs,
    }
    return render(request, "v2/generic/data_entry_form.html", context=context)


def threat_object_delete(request):
    obj = ThreatReference.objects.get(id=link_id)
    obj.delete()
    # messages.success(request, "Campaign successfully deleted.")
    return redirect("threat_db")
