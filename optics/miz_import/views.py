import json
from zipfile import BadZipFile
from anytree.exporter import JsonExporter
from anytree.importer import JsonImporter
from django.contrib.auth.decorators import login_required
from django.core.files.uploadhandler import TemporaryFileUploadHandler
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt, csrf_protect
from django.views.decorators.http import require_http_methods
import apps.miz_import.util as util
from ..airops.models import Package
from django.contrib.auth import get_user_model


@login_required(login_url="account_login")
def import_initial(request, packageId: str):
    # Initial entry point to importing dcs mission file.
    #  Following naviagtion handled by htmx and returns only partials.
    request.session["return_url"] = reverse("package_v2", args={packageId})
    request.session["package_id"] = packageId
    context = {
        "return_url": request.GET.get("returnUrl"),
    }
    return render(request, "miz_import/import.html", context)


@login_required(login_url="account_login")
def upload_file_init(request):
    return render(request, "miz_import/htmx/upload_file.html")


def test_modal(request, link_id):
    return render(request, f"miz_import/htmx/test_modal{link_id}.html")


@login_required(login_url="account_login")
def view_tree(request):
    tree = request.session["full_tree"]
    if tree:
        context = {"tree": tree}
        return render(request, "miz_import/view_tree.html", context)
    context = {"alert_text": "No file uploaded"}
    return render(request, "miz_import/htmx/upload_file.html", context=context)


# https://docs.djangoproject.com/en/3.2/topics/http/file-uploads/#modifying-upload-handlers-on-the-fly-1
@require_http_methods(["POST"])
@csrf_exempt
def upload_mission_file(request):
    """Swap to the temp file upload handler to avoid problems with memory useage on large miz files."""
    request.upload_handlers.insert(0, TemporaryFileUploadHandler(request))
    return _upload_mission_file(request)


@csrf_protect
def _upload_mission_file(request):
    if request.method == "POST" and len(request.FILES):
        mission_file = request.FILES["file"]
        if mission_file.name[-3:] != "miz":
            return render(
                request,
                "miz_import/htmx/upload_file.html",
                context={"alert_text": "file type must be .miz"},
            )
        try:
            mission_tree, parse_msgs = create_mission_tree(mission_file)
        except KeyError as ex:
            return HttpResponse(f"Mission File Parse Error: {ex}")
        except BadZipFile as ex:
            return HttpResponse(f"Mission File Exception: {ex}")

        # Store the mission details in the session.
        request.session["full_tree"] = JsonExporter().export(mission_tree)

        messages = []
        for msg in parse_msgs:
            messages.append(msg.message)
        context = {
            "parse_messages": messages,
            "mission_text": mission_tree.text,
            "package_id": request.session["package_id"],
            "return_url": request.session["return_url"],
        }

        return render(request, "miz_import/htmx/upload_results.html", context=context)
    return render(
        request,
        "miz_import/htmx/upload_file.html",
        context={"alert_text": "No file uploaded"},
    )


def create_mission_tree(mission_file) -> tuple:
    with mission_file:
        mission, parse_msg = util.load_external_mission(
            mission_file.temporary_file_path()
        )
    mission_tree = util.build_client_air_units_tree(mission)
    return mission_tree, parse_msg


@require_http_methods(["POST"])
@login_required()
def import_to_package(request):
    package = get_object_or_404(Package, pk=request.session["package_id"])
    # flights = package.flight_set.all()
    user = get_object_or_404(get_user_model(), pk=request.user.pk)
    selected_items = json.loads(request.POST["selected"])  # list
    importer = JsonImporter()
    ft = request.session.get("full_tree")
    full_root = importer.import_(ft)
    package = util.add_to_package(full_root, selected_items, package)
    package.save()
    request.session["full_tree"] = ""
    return redirect("package_v2", link_id=package.pk)


def test_htmx1(request):
    return render(request, "miz_import/htmx/test_base.html")


def test_htmx2(request):
    return render(request, "miz_import/htmx/test_partial2.html")


"""
modal wih htmx
https://github.com/bblanchon/django-htmx-modal-form

progress bar upload for future?
https://github.com/ouhouhsami/django-progressbarupload

"""
