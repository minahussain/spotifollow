from django.db import models

class Search(models.Model):
	playlist_id = models.CharField(max_length=200)
	title = models.CharField(max_length=200)
	author = models.CharField(max_length=200)
	total = models.IntegerField()
	href = models.CharField(max_length=200)
	tracks_href = models.CharField(max_length=200)
