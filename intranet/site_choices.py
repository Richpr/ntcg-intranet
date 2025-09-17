# intranet/site_choices.py

from django.db import models

class Phase(models.Model):
    name = models.CharField(max_length=100, unique=True)
    def __str__(self):
        return self.name

class Batch(models.Model):
    name = models.CharField(max_length=100, unique=True)
    def __str__(self):
        return self.name

class RadioType(models.Model):
    name = models.CharField(max_length=100, unique=True)
    def __str__(self):
        return self.name
        
class AntennaType(models.Model):
    name = models.CharField(max_length=100, unique=True)
    def __str__(self):
        return self.name

class EnclosureType(models.Model):
    name = models.CharField(max_length=100, unique=True)
    def __str__(self):
        return self.name

class BBML(models.Model):
    name = models.CharField(max_length=100, unique=True)
    def __str__(self):
        return self.name

class ProjectScope(models.Model):
    name = models.CharField(max_length=100, unique=True)
    def __str__(self):
        return self.name
    
class SiteStatus(models.Model):
    name = models.CharField(max_length=50, unique=True)
    def __str__(self):
        return self.name

class QAStatus(models.Model):
    name = models.CharField(max_length=50, unique=True)
    def __str__(self):
        return self.name