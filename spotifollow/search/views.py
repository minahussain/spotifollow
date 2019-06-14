from django.shortcuts import render_to_response, redirect, render

from .models import Search

from django.views import generic
from django.views import View

from playlist.views import process_request
from playlist.views import link_list
from playlist.views import PlaylistListView
from playlist.views import PlaylistDetailView
from playlist.views import index
from playlist.views import refresh_list
from playlist.views import process_tracks

from playlist.models import Playlist
from playlist.models import Track
from playlist.models import TrackInstance

from playlist.forms import LinkedPlaylistForm

from django.urls import reverse

from django.contrib import messages

import requests
import re

# make the origin playlist if it does not exist from the search data
def link_playlists(request):
	if request.method == 'POST':
		form = LinkedPlaylistForm(request.POST)
		if form.is_valid():
			user_title = form.cleaned_data['user_title']
			origin_id = form.cleaned_data['playlist_id']
			user_playlist = Playlist.objects.get(title=user_title)
			try:
				origin_playlist = Playlist.objects.get(playlist_id=origin_id)
			except Playlist.DoesNotExist:
				ret = form.save()
				origin_playlist = Playlist.objects.get(playlist_id=origin_id)

			if user_playlist and origin_playlist:
				refresh_list(request, origin_playlist.playlist_id)
				user_playlist.set_origin_playlist(origin_playlist)
				return redirect(reverse('playlist-detail', kwargs={'list_id':user_playlist.playlist_id}))
		else:
			try:
				user_playlist = Playlist.objects.get(title=form.data['user_title'])
				origin_playlist = Playlist.objects.get(playlist_id=form.data['playlist_id'])
				refresh_list(request, origin_playlist.playlist_id)
				user_playlist.set_origin_playlist(origin_playlist)
				return redirect(reverse('playlist-detail', kwargs={'pk':user_playlist.playlist_id}))
			except Playlist.DoesNotExist:
				pass
	messages.error(request, form.errors)
	return redirect('playlists')

class SearchDetailView(generic.DetailView):
	model = Search

	def get_context_data(self, **kwargs):
		context = super(SearchDetailView, self).get_context_data(**kwargs)
		context['playlist_list'] = Playlist.objects.filter(author=self.request.user)
		return context

class SearchListView(generic.ListView):
	context_object_name = 'search_list'

	def get_queryset(self):
		Search.objects.all().delete() # each request is new queryset
		query = self.request.GET.get('title')
		if query:
			query = re.sub(r"\s", r"\+", query)
			url = 'https://api.spotify.com/v1/search?q=' + query + '&type=playlist&limit=50'
			search_data = process_request(self.request, 'get', url)
			data_total = search_data['playlists']['total']

			for curr_search in search_data['playlists']['items']:
				title = curr_search['name']
				author = curr_search['owner']['display_name']
				if author is not None:
					href = curr_search['href']
					playlist_id = curr_search['id']
					tracks_href = curr_search['tracks']['href']
					tracks_total = curr_search['tracks']['total']
					search_obj, created = Search.objects.get_or_create(
						playlist_id=playlist_id,
						title=title,
						author=author,
						total=tracks_total,
						href=href,
						tracks_href=tracks_href,
					)
		return Search.objects.all()

	def get_context_data(self, **kwargs):
		context = super(SearchListView, self).get_context_data(**kwargs)
		context['playlist_list'] = Playlist.objects.filter(author=self.request.user)
		return context


