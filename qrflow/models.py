import uuid

from django.db import models

class Location(models.Model):
    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    place_id = models.CharField(max_length=200)  # Google Place ID

    def __str__(self):
        return self.name


class Feedback(models.Model):
    location_slug = models.CharField(max_length=200, null=True, blank=True)

    what_went_wrong = models.TextField()
    email = models.EmailField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.location_slug} - {self.created_at:%Y-%m-%d %H:%M}"