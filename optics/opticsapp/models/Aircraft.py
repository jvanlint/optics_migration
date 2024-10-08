from django.db import models
from django.contrib.auth.models import User


class Aircraft(models.Model):
    # Fields

    type = models.ForeignKey("Airframe", on_delete=models.CASCADE, null=True)
    flight = models.ForeignKey("Flight", on_delete=models.CASCADE, null=True)
    pilot = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="user_pilot",
    )
    rio_wso = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="user_rio",
        verbose_name="WSO/RIO",
    )
    tailcode = models.CharField(
        max_length=20,
        help_text="Enter A/C tail code.",
        null=True,
        blank=True,
        verbose_name="Tail Code",
    )

    lasercode = models.CharField(
        max_length=10,
        help_text="Enter A/C laser code.",
        null=True,
        blank=True,
        verbose_name="Laser Code",
    )

    flight_lead = models.BooleanField(default=False, verbose_name="Flight Lead")
    package_lead = models.BooleanField(default=False, verbose_name="Package Lead")

    # Metadata

    class Meta:
        ordering = ["-flight_lead", "-pilot"]
        verbose_name = "Aircraft"
        verbose_name_plural = "Aircraft"

    # Methods

    def multicrew(self):
        return self.type.multicrew

    def new(self, flightObject):
        new_aircraft_instance = Aircraft(
            type=self.type,
            flight=flightObject,
        )
        new_aircraft_instance.save()

    def copy(self):
        flightID = self.flight.id

        self.new(self.flight)

        return flightID

    def copyToFlight(self, flight):
        self.new(flight)
