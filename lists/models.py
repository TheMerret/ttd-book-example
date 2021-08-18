from django.db import models
from django.core.urlresolvers import reverse


# Create your models here.
class List(models.Model):
    """список"""

    def get_absolute_url(self):
        """получить абсолютный url"""
        return reverse('view_list', args=[self.id])

    @staticmethod
    def create_new():
        """создать новый"""
        pass


class Item(models.Model):
    """элемент списка"""
    text = models.TextField(default='')
    list = models.ForeignKey(List, default=None)

    class Meta:
        ordering = ('id', )
        unique_together = ('list', 'text')

    def __str__(self):
        return self.text