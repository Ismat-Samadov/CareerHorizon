from django.db import models
from users.models import CustomUser
from django.conf import settings
from django.core.files.storage import default_storage
from django.db import models
from payments.models import Order

class JobPost(models.Model):
    title = models.CharField(max_length=500)
    description = models.TextField()
    company = models.CharField(max_length=500)
    location = models.CharField(max_length=500)
    function = models.CharField(max_length=500, blank=True, null=True)
    schedule = models.CharField(max_length=500, blank=True, null=True)
    deadline = models.DateField(blank=True, null=True)
    responsibilities = models.TextField(blank=True, null=True)
    requirements = models.TextField(blank=True, null=True)
    posted_by = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='job_posts')
    posted_at = models.DateTimeField(auto_now_add=True)
    deleted = models.BooleanField(default=False)
    is_scraped = models.BooleanField(default=False)
    is_premium = models.BooleanField(default=False)
    premium_days = models.IntegerField(default=0)
    priority_level = models.IntegerField(default=0)
    apply_link = models.URLField(max_length=1000, default='')
    # New fields for payment integration
    is_paid = models.BooleanField(default=False)
    posting_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    payment_order = models.ForeignKey(Order, on_delete=models.SET_NULL, null=True, blank=True, related_name='job_post')  # Link to the payment order

    def __str__(self):
        return self.title

class JobApplication(models.Model):
    job = models.ForeignKey(JobPost, on_delete=models.CASCADE)
    full_name = models.CharField(max_length=255, blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=15, blank=True)
    cover_letter = models.TextField(blank=True, null=True)
    applied_at = models.DateTimeField(auto_now_add=True)
    resume = models.FileField(upload_to='resumes/')
    match_score = models.FloatField(blank=True, default=0.0) 

    def __str__(self):
        return f'{self.full_name} - {self.job.title}'

    def match_score_percentage(self):
        """Convert match score to a percentage"""
        if self.match_score is not None:
            return round(self.match_score * 100, 2)
        return None
