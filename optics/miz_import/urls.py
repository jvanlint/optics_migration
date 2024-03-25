from django.urls import path

from optics.miz_import import views

# fmt: off
urlpatterns = [
    path('initial/<int:packageId>', views.import_initial, name='miz_import_initial'),
    path('upload_miz', views.upload_mission_file, name='upload_miz'),
    path('reset_file_upload', views.upload_file_init, name='upload_file_init'),
    path('view_tree', views.view_tree, name='view_tree'),
    path('import_to_package', views.import_to_package, name='import_to_package'),
    
    # path('test_post', views.test_post, name='test_post'),
    path('test_modal/<int:link_id>', views.test_modal, name='test_modal'),
    
    path('test/htmx1', views.test_htmx1, name='test_htmx1'),
    path('test/htmx2', views.test_htmx2, name='test_htmx2'),
    
]
# fmt: on
