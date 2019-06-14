from django import forms
from .models import Playlist

class LinkedPlaylistForm(forms.ModelForm):
	user_title =  forms.CharField(max_length=200)

	class Meta:
		model = Playlist
		fields = ['playlist_id', 'title', 'author', 'href', 'tracks_href']