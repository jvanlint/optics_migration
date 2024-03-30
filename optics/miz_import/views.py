import json
from zipfile import BadZipFile

from anytree.exporter import JsonExporter
from anytree.importer import JsonImporter
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.files.uploadhandler import TemporaryFileUploadHandler
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt, csrf_protect
from django.views.decorators.http import require_http_methods

from optics.miz_import import mission_parser, tree_parser
from optics.opticsapp.models import Package


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
        mission, parse_msg = mission_parser.load_external_mission(
            mission_file.temporary_file_path()
        )
    mission_tree = mission_parser.parse_mission_to_tree(mission)
    return mission_tree, parse_msg


@require_http_methods(["POST"])
@login_required()
def import_to_package(request):
    package = get_object_or_404(Package, pk=request.session["package_id"])
    selected_items = json.loads(
        request.POST["selected"]
    )  # list of things to import to this package
    importer = JsonImporter()
    # ft = request.session.get("full_tree")
    full_tree = importer.import_(request.session.get("full_tree"))
    try:
        package = tree_parser.add_to_package(full_tree, selected_items, package)
    except Exception as e:
        messages.error(request, f"Error adding to package: {e}")
        return redirect("package_v2", link_id=package.pk)
        #  TDOD: Fix messages on pages with htmx.
        #  https://www.youtube.com/watch?v=T7TgfRiRb10
        # https://github.com/bblanchon/django-htmx-messages-framework
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
