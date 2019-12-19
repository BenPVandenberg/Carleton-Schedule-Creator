from django.db import models


# Create your models here.

class Course(models.Model):
    status = models.CharField(max_length=30)
    crn = models.CharField(max_length=10,primary_key=True)
    code = models.CharField(max_length=10)
    section = models.CharField(max_length=5)
    name = models.CharField(max_length=100)
    credits = models.FloatField()
    type = models.CharField(max_length=10)
    instructor = models.CharField(max_length=30)
    days = models.CharField(max_length=50)
    time = models.CharField(max_length=50)
    reqs = models.CharField(max_length=100)
    length = models.FloatField()

    def __str__(self):
        return self.code + ' ' + self.section
