from django.db import models


class SiteSettings(models.Model):

    booking_days_in_advance = models.PositiveIntegerField(default=3)

    opening_time = models.TimeField(
        default="12:00",
        help_text="Earliest reservable time."
    )

    closing_time = models.TimeField(
        default="22:00",
        help_text="Latest reservable time."
    )

    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

