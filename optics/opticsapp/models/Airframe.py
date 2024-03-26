import csv

from django.contrib.auth.models import User
from django.db import models


def get_airframes():
    with open("optics/DCS_airframes.txt") as file:
        for row in csv.reader(file):
            yield (row[0], row[1])


class Airframe(models.Model):
    # Choices:
    # Run make_choices.py to generate the following list when new aircraft/helos added to DCS

    # Fields

    name = models.CharField(max_length=200, help_text="Enter Airframe Name")
    stations = models.IntegerField(default=2)
    multicrew = models.BooleanField(default=False)
    date_created = models.DateTimeField(auto_now_add=True, null=True)
    date_created.hidden = True
    date_modified = models.DateTimeField(auto_now=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    dcs_mapping = models.CharField(
        max_length=50, choices=get_airframes, default="Not_Mapped"
    )

    # Metadata

    class Meta:
        ordering = ["name"]

    # Methods

    def __str__(self):
        return self.name
