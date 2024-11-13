import json
import logging
import random
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

from optics.miz_import import tree_parser
from optics.opticsapp.models import Package
from optics.miz_import.pydcs_mission import DCSMission
from .forms import UploadFileForm

logger = logging.getLogger(__name__)


@login_required(login_url="account_login")
def import_initial(request, packageId: str):
    # Initial entry point to importing dcs mission file.
    #  Following naviagtion handled by htmx and returns only partials.
    form = UploadFileForm()
    request.session["return_url"] = reverse("package_v2", args={packageId})
    request.session["package_id"] = packageId
    context = {
        "return_url": request.GET.get("returnUrl"),
        "form": form,
    }
    return render(request, "miz_import/import.html", context)


@login_required(login_url="account_login")
def upload_file_init(request):
    return render(request, "miz_import/partials/upload_file.html")


def test_modal(request, link_id):
    return render(request, f"miz_import/htmx/test_modal{link_id}.html")


@login_required(login_url="account_login")
def view_tree(request):
    tree = request.session["full_tree"]
    if tree:
        context = {"tree": tree}
        return render(request, "miz_import/view_tree.html", context)
    context = {"alert_text": "No file uploaded"}
    return render(request, "miz_import/import.html", context=context)


@require_http_methods(["POST"])
@csrf_exempt
def upload_mission_file(request):
    """Swap to the temp file upload handler to avoid problems with memory useage on large miz files."""
    # https://docs.djangoproject.com/en/3.2/topics/http/file-uploads/#modifying-upload-handlers-on-the-fly-1
    request.upload_handlers.insert(0, TemporaryFileUploadHandler(request))
    return _upload_mission_file(request)


@csrf_protect
def _upload_mission_file(request):
    if request.method == "POST":
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():

            mission_file = request.FILES["file"]
            if mission_file.name[-3:] != "miz":
                messages.error(request, f"File must be a .miz")

            try:
                mission_tree, parse_msgs = create_mission_tree(mission_file)
            except KeyError as ex:
                return HttpResponse(f"Mission File Parse Error: {ex}")
            except BadZipFile as ex:
                return HttpResponse(f"Mission File Exception: {ex}")

            # Store the mission details in the session.
            request.session["full_tree"] = JsonExporter().export(mission_tree)

            # messages = []
            # for msg in parse_msgs:
            #     messages.append(msg.message)
            context = {
                # "parse_messages": messages,
                "mission_text": mission_tree.text,
                "package_id": request.session["package_id"],
                "return_url": request.session["return_url"],
            }

            return render(request, "miz_import/after_import.html", context=context)
        return render(
            request,
            "miz_import/import.html",
            context={"alert_text": "No file uploaded"},
        )


def create_mission_tree(mission_file) -> tuple:
    with mission_file:
        mission = DCSMission()
    # optics/miz_import/tests/missions/test.miz
        parse_msg = mission.load_file(mission_file)
        mission_tree = mission.to_tree()
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
        logger.warning(e)
        return HttpResponse(f"Error adding to package: {e}")
        # return redirect("package_v2", link_id=package.pk)
        #  TDOD: Fix messages on pages with htmx.
        #  https://www.youtube.com/watch?v=T7TgfRiRb10
        # https://github.com/bblanchon/django-htmx-messages-framework
    package.save()
    request.session["full_tree"] = ""
    return redirect("package_v2", link_id=package.pk)


def test_htmx1(request):
    return render(request, "miz_import/htmx_tests/test_base.html")


def test_htmx2(request):
    return render(request, "miz_import/htmx_tests/test_partial2.html")


SAMPLE_MESSAGES = [
    (messages.DEBUG, "Hello World!"),
    (messages.INFO, "System operational"),
    (messages.SUCCESS, "Congratulations! You did it."),
    (messages.WARNING, "Hum... not sure about that."),
    (messages.ERROR, "Oops! Something went wrong"),
]


def test_toast(request):
    messages.add_message(request, *random.choice(SAMPLE_MESSAGES))
    return render(request, "miz_import/partials/alerts.html")


# def test_toast(request):
#     messages.error(request, "this is a message")
#     return render(request, "miz_import/partials/toast.html")


def test_htmx(request, pageNumber):
    match pageNumber:
        case 1:
            return render(request, "miz_import/partials/test1.html")
        case 2:
            return render(request, "miz_import/partials/test2.html")
        case 3:
            return render(request, "miz_import/partials/test3.html")
        case _:
            return render(request, "miz_import/htmx_tests/test_base.html")


"""
flash messages for the site with htmx?
https://danjacob.net/posts/htmx_messages/
https://github.com/danjac/django_htmx_messages
https://github.com/bblanchon/django-htmx-messages-framework/tree/hx-trigger



modal wih htmx
https://github.com/bblanchon/django-htmx-modal-form

progress bar upload for future?
https://github.com/ouhouhsami/django-progressbarupload

"""
