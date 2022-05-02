import uuid

import django
from django.db import models


class RelatedSlugIdModel(models.Model):
    id = models.SlugField(default=uuid.uuid4, primary_key=True)
    text = models.CharField(max_length=100)


class RelatedIntIdModel(models.Model):
    text = models.CharField(max_length=100)


class DateFieldModel(models.Model):
    date = models.DateField()
    datetime = models.DateTimeField()
    time = models.TimeField()


class BooleanModel(models.Model):
    flag = models.BooleanField(default=False)
    if django.VERSION < (4, 0):
        null_flag = models.NullBooleanField(default=None)
    else:
        null_flag = models.BooleanField(null=True)


class NumberModel(models.Model):
    number = models.IntegerField(default=0)
    float = models.FloatField()
    decimal = models.DecimalField(max_digits=5, decimal_places=2)


class EmailModel(models.Model):
    email = models.EmailField()


class URLModel(models.Model):
    url = models.URLField()


class IpModel(models.Model):
    ip = models.GenericIPAddressField()


class TestAbstractModel(models.Model):
    char = models.CharField(max_length=100)
    text = models.TextField()

    class Meta:
        abstract = True


class TextModel(TestAbstractModel):
    CHOICES = (
        ('a', 'A'),
        ('b', 'B'),
        ('c', 'C'),
    )
    choice = models.CharField(choices=CHOICES, max_length=1)
    slug = models.SlugField(max_length=200)
    slug_fk = models.ForeignKey(to=RelatedSlugIdModel, null=True, on_delete=models.SET_NULL)
    int_fk = models.ForeignKey(to=RelatedIntIdModel, null=True, on_delete=models.SET_NULL)
