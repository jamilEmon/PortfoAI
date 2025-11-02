from django.db import models

# Create your models here.
class Review(models.Model):
    site_url = models.CharField(max_length=10000)
    site_image_url = models.CharField(max_length=10000)
    feedback = models.CharField(max_length=1000000, default=None, null=True)

    GREAT_POOR_CHOICES = (
        ('great', 'Great'),
        ('poor', 'Poor'),
    )

    user_rating = models.CharField(
        max_length=5,
        choices=GREAT_POOR_CHOICES,
        default=None,
        null=True,
        blank=True
    )

    class Meta:
        app_label = 'review'