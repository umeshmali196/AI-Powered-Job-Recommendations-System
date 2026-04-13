from django.db import models
from django.contrib.auth.models import User
from jobs.models import Job

class Recommendation(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    job = models.ForeignKey(Job, on_delete=models.CASCADE)
    match_score = models.FloatField()

    def __str__(self):
        return f"{self.user.username} - {self.job.title}"