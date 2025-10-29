from django.db import models
from locations.models import Location

class MenuDocument(models.Model):
    title = models.CharField(max_length=200)
    location = models.ForeignKey(Location, related_name='menus', on_delete=models.CASCADE)
    pdf = models.FileField(upload_to='menus/')  # upload your PDFs to MEDIA/menus/
    sort_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['location', 'sort_order', 'title']

    def __str__(self):
        return f"{self.location.name} – {self.title}"
