from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit
from django import forms


class UploadFileForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_id = 'uploadFile'
        self.helper.form_class = 'blueForms'
        self.helper.form_method = 'post'
        self.helper.form_action = 'upload_miz'

        self.helper.add_input(Submit('submit', 'Submit'))

    file = forms.FileField(
        label='Select a mission (/miz) file',
        help_text="Select the dcs mission file to upload.",
        error_messages={"required": "Choose the mission file to upload"},
    )
