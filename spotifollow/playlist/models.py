from django.db import models

class Track(models.Model):
	track_id = models.CharField(max_length=200, primary_key=True)
	title = models.CharField(max_length=200)
	artist = models.CharField(max_length=200)
	artist_id = models.CharField(max_length=200)
	href = models.CharField(max_length=500)

	def __str__(self):
		return self.title + ' by ' + self.artist

class Playlist(models.Model):
	playlist_id = models.CharField(max_length=200, primary_key=True)
	title = models.CharField(max_length=200)
	author = models.CharField(max_length=200)
	href = models.CharField(max_length=500)
	tracks_href = models.CharField(max_length=200)
	tracks = models.ManyToManyField(Track, through='TrackInstance')
	linked = models.BooleanField(default=False)
	origin_playlist = models.ForeignKey('self', null=True, on_delete=models.SET_NULL)

	def tracks_ordered(self):
		return TrackInstance_set(playlist=self).order_by(title)

	def added_tracks_set(self):
		return self.tracks.filter(trackinstance__status='AD')

	def deleted_tracks_set(self):
		return self.tracks.filter(trackinstance__status='DE')

	def kept_tracks_set(self):
		return self.tracks.filter(trackinstance__status='KP')

	def tracks_count(self):
		return self.tracks.exclude(trackinstance__status='DE').count()

	def added_tracks_count(self):
		return self.tracks.filter(trackinstance__status='AD').count()

	def deleted_tracks_count(self):
		return self.tracks.filter(trackinstance__status='DE').count()

	def kept_tracks_count(self):
		return self.tracks.filter(trackinstance__status='KP').count()

	def is_linked(self):
		return self.linked == True

	def add_track(self, track):
		try:
			track_inst = TrackInstance.objects.get(playlist=self, track=track)
			if track_inst.is_deleted():
				track_inst.set_status_kept()
				track_inst.save()
		except TrackInstance.DoesNotExist:
			track_inst = TrackInstance.objects.create(playlist=self, track=track)
			track_inst.set_status_add()
			track_inst.save()

	def delete_track(self, track):
		try:
			track_inst = TrackInstance.objects.get(playlist=self, track=track)
		except TrackInstance.DoesNotExist:
			return TrackInstance.DoesNotExist

		if track_inst.is_added():
			track_inst.delete()
		else:
			track_inst.set_status_del()
			track_inst.save()

	# check user list's songs against original list
	# either they are added, kept, or deleted
	def link_list(self, origin_playlist):
		user_tracks = self.tracks.all()
		origin_tracks = origin_playlist.tracks.all()

		added_tracks = user_tracks.difference(origin_tracks)
		deleted_tracks = origin_tracks.difference(user_tracks)

		self.linked = True
		self.origin_playlist = origin_playlist

		for added_track in added_tracks:
			track_inst = TrackInstance.objects.get(playlist=self, track=added_track)
			track_inst.set_status_add()
			track_inst.save()

		for deleted_track in deleted_tracks:
			track_inst, created = TrackInstance.objects.get_or_create(playlist=self, track=deleted_track)
			track_inst.set_status_del()
			track_inst.save()

		self.save()

	# unlink if is linked, remove origin playlist
	def unlink_list(self):
		if self.linked:
			trackinst_set = TrackInstance.objects.filter(playlist=self)
			trackinst_set.filter(status='DE').delete()
			trackinst_set.update(status='KP')
			self.linked = False
			self.origin_playlist = None
			self.save()

	def set_origin_playlist(self, origin_playlist):
		if not self.linked:
			self.link_list(origin_playlist)
		
	def get_absolute_url(self):
	    """Returns the url to access a particular instance of the model."""
	    return reverse('playlist-detail', args=[str(self.id)])

	def __str__(self):
		return self.title + ' by ' + self.author

class TrackInstance(models.Model):
	KEPT = 'KP'
	DELETED = 'DE'
	ADDED = 'AD'
	TRACK_STATUS_CHOICES = (
		(KEPT, 'kept'),
		(DELETED, 'deleted'),
		(ADDED, 'added'),
	)

	track = models.ForeignKey(Track, on_delete=models.SET_NULL, null=True)
	playlist = models.ForeignKey(Playlist, on_delete=models.SET_NULL, null=True)
	status = models.CharField(
		max_length=2,
		choices=TRACK_STATUS_CHOICES, 
		default=KEPT,
	)

	def set_status_del(self):
		self.status = self.DELETED

	def set_status_add(self):
		self.status = self.ADDED

	def set_status_kept(self):
		self.status = self.KEPT
		
	def is_added(self):
		return self.status == self.ADDED

	def is_deleted(self):
		return self.status == self.DELETED

	def is_kept(self):
		return self.status == self.KEPT

	def is_removeable(self):
		return self.status in (self.KEPT, self.ADDED)

	def is_original(self):
		return self.status in (self.KEPT, self.DELETED)

	def __str__(self):
		return self.track.title + ' by ' + self.track.artist + ' on ' + self.playlist.title
