from django.db import models

# Create your models here.
class User(models.Model):
    name = models.CharField(max_length=100, primary_key=True)
    password = models.CharField(max_length=100)

    def __str__(self):
        return self.name
    


class Result(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100)
    result = models.IntegerField()
    detail = models.CharField(max_length=1000)
    comment = models.CharField(max_length=1000)
    save_path = models.CharField(max_length=1000)
    time = models.CharField(max_length=1000)

    def __str__(self):
        return str(self.id) + " " + self.name