from .models import Playlist
from .models import Track
from .models import TrackInstance

from django.views import generic
from django.views import View

from django.shortcuts import redirect, render
from django.contrib.auth import logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from django.urls import reverse

from django.http import HttpResponseRedirect
from django.http import Http404

import requests
import re
import json
import sys

from social_django.utils import load_strategy

'''
	Tools
'''
def process_request(request, type, url, body=''):
	if request.user:
		social = request.user.social_auth.get(provider='spotify')
		tok = social.get_access_token(load_strategy())
		head = {'Authorization': 'Bearer ' + tok} 
		if type.upper() == 'GET':
			response = requests.get(url, headers=head)
		elif type.upper() == 'POST':
			response = requests.post(url, headers=head)
		else:
			head['Content-Type'] = 'application/json'
			response = requests.delete(url, data=body, headers=head)
		data = response.json()
		return data
	else:
		return {}

'''
	Basic
'''
def index(request):
	return render(request, "index.html")

def logout(request):
    auth_logout(request)
    return HttpResponseRedirect('index.html')


'''
	Views
'''

class PlaylistListView(generic.ListView):
	model = Playlist
	context_object_name = 'playlist_list'

	def get_context_data(self, **kwargs):
		context = super(PlaylistListView, self).get_context_data(**kwargs)
		context['playlist_list'] = Playlist.objects.filter(author=self.request.user)
		return context

class PlaylistDetailView(generic.DetailView):
    model = Playlist

    def get_context_data(self, **kwargs):
        context = super(PlaylistDetailView, self).get_context_data(**kwargs)
        context['playlist_list'] = Playlist.objects.filter(author=self.request.user)
        return context

'''
	Spotify / Playlist Functions 
'''

def get_user_playlists(request):
	if request.user:
		username = request.user.get_username()
		url = 'https://api.spotify.com/v1/users/' + username + '/playlists'
		playlists_data = process_request(request, 'get', url)

		# save playlists and their tracks
		for i in range(int(playlists_data['total'])):
			curr_playlist = playlists_data['items'][i]
			title = curr_playlist['name']
			href = curr_playlist['href']
			playlist_id = curr_playlist['id']
			tracks_href = curr_playlist['tracks']['href']
			playlist_obj, created = Playlist.objects.get_or_create(
				playlist_id=playlist_id,
				title=title,
				author=username,
				href=href,
				tracks_href=tracks_href,
			)
			if created:
				tracks_data = process_request(request, 'get', tracks_href)

				for i in range(int(tracks_data['total'])):
					curr_track = tracks_data['items'][i]['track']
					track_title = curr_track['name']
					track_id = curr_track['id']
					track_artist = curr_track['artists'][0]['name']
					artist_id = curr_track['artists'][0]['id']
					href = curr_track['href']
					track_obj, created = Track.objects.get_or_create(
							track_id=track_id,
							title=track_title,
							artist=track_artist,
							artist_id=artist_id,
							href=href,
						)
					TrackInstance.objects.get_or_create(track=track_obj, playlist=playlist_obj)
	# playlist_list = Playlist.objects.all()
	return HttpResponseRedirect(reverse('playlists'))

# helper for refresh_list function
def process_tracks(tracks_data, playlist):
	for i in range(int(tracks_data['total'])):
		curr_track = tracks_data['items'][i]['track']
		track_title = curr_track['name']
		track_id = curr_track['id']
		track_artist = curr_track['artists'][0]['name']
		artist_id = curr_track['artists'][0]['id']
		href = curr_track['href']
		track_obj = playlist.tracks.filter(track_id=track_id)
		if not track_obj.exists():
			track, created = Track.objects.get_or_create(
				track_id=track_id,
				title=track_title,
				artist=track_artist,
				artist_id=artist_id,
				href=href,
			)
			TrackInstance.objects.get_or_create(track=track, playlist=playlist)
	return

# adds any new songs the user and original playlist has since last update
# keeps songs user personally added and deleted
def refresh_list(request, list_id):
	playlist = Playlist.objects.get(playlist_id=list_id)
	tracks = playlist.tracks

	# refresh user playlist
	url = 'https://api.spotify.com/v1/playlists/' + playlist.playlist_id + '/tracks'
	user_tracks_data = process_request(request, 'get', url)
	process_tracks(user_tracks_data, playlist)
	
	# compare user playlist against original playlist
	if playlist.is_linked():
		url = 'https://api.spotify.com/v1/playlists/' + playlist.origin_playlist.playlist_id + '/tracks'
		origin_tracks_data = process_request(request, 'get', url)
		process_tracks(origin_tracks_data, playlist.origin_playlist)
		playlist.link_list(playlist.origin_playlist)

	return HttpResponseRedirect(reverse('playlist-detail', kwargs={'pk':list_id}))

def delete_track(request, list_id, track_id):
	playlist = Playlist.objects.get(playlist_id=list_id)
	track = Track.objects.get(track_id=track_id)
	try:
		playlist.delete_track(track)
	except TrackInstance.DoesNotExist:
		raise Http404('This track was not able to be deleted.')

	# DELETE FROM SPOTIFY
	url = 'https://api.spotify.com/v1/playlists/' + playlist.playlist_id + '/tracks'
	track_uri_dict = {"uri": "spotify:track:" + track.track_id} 
	body_dict = {"tracks": [track_uri_dict]}
	data = process_request(request, 'delete', url, json.dumps(body_dict))
	return HttpResponseRedirect(reverse('playlist-detail', kwargs={'pk':list_id}))

def add_track(request, list_id, track_id):
	playlist = Playlist.objects.get(playlist_id=list_id)
	track = Track.objects.get(track_id=track_id)
	playlist.add_track(track)
	# ADD TO SPOTIFY
	url = 'https://api.spotify.com/v1/playlists/' + playlist.playlist_id + '/tracks?uris=spotify:track:' + track.track_id
	process_request(request, 'post', url)
	return HttpResponseRedirect(reverse('playlist-detail', kwargs={'pk':list_id}))

# adding origin playlist
def link_list(request, user_list_id, origin_list_id):
	playlist = Playlist.objects.get(playlist_id=user_list_id)
	origin_playlist = Playlist.objects.get(playlist_id=origin_list_id)
	playlist.set_origin_playlist(origin_playlist)
	return HttpResponseRedirect(reverse('playlist-detail', kwargs={'pk':user_list_id}))

# removing origin playlist
def unlink_list(request, user_list_id, origin_list_id):
	playlist = Playlist.objects.get(playlist_id=user_list_id)
	playlist.unlink_list()
	return HttpResponseRedirect(reverse('playlist-detail', kwargs={'pk':user_list_id}))
		



