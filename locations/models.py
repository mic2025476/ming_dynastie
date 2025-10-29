from django.db import models

class Location(models.Model):
    name = models.CharField(max_length=120)
    slug = models.SlugField(unique=True)
    address = models.TextField()
    phone = models.CharField(max_length=50, blank=True)
    email = models.EmailField(blank=True)
    opening_hours = models.CharField(max_length=200, blank=True)
    menu_pdf = models.URLField(blank=True)
    order_url = models.URLField(blank=True)
    map_url = models.URLField(blank=True)
    hero_image = models.ImageField(upload_to='locations/', blank=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name
