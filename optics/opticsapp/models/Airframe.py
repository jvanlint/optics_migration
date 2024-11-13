from django.contrib.auth.models import User
from django.db import models


class DCSAirframe(models.Model):
    dcsname = models.CharField(max_length=50, primary_key=True, unique=True)

    def __str__(self):
        return self.dcsname


class Airframe(models.Model):
    name = models.CharField(max_length=200, help_text="Enter Airframe Name")
    stations = models.IntegerField(default=2)
    multicrew = models.BooleanField(default=False)
    date_created = models.DateTimeField(auto_now_add=True, null=True)
    date_created.hidden = True
    date_modified = models.DateTimeField(auto_now=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    dcsname = models.OneToOneField(
        DCSAirframe, on_delete=models.SET_NULL, null=True, blank=True
    )

    class Meta:
        ordering = ["name"]

    # Methods

    def __str__(self):
        return self.name


# https://docs.djangoproject.com/en/5.0/topics/db/examples/one_to_one/
