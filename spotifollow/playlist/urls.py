from django.urls import path
from django.conf.urls import include, url
from django.contrib.auth import logout 
from . import views

urlpatterns = [
	path('', views.index, name='index'),
	path(r'^logout/$', views.logout, name='logout'),
	path('delete/<list_id>/<track_id>', views.delete_track, name='delete'),
	path('add/<list_id>/<track_id>', views.add_track, name='add'),
	path('playlist/<list_id>/refresh/', views.refresh_list, name='refresh'),
	path('playlists/<user_list_id>/link/<origin_list_id>', views.link_list, name='link-list'),
	path('playlists/<user_list_id>/unlink/<origin_list_id>', views.unlink_list, name='unlink-list'),
	path('playlists/', views.PlaylistListView.as_view(), name='playlists'),
	path('playlist/<slug:pk>', views.PlaylistDetailView.as_view(), name='playlist-detail'),
	path('playlists/list/', views.get_user_playlists, name='get-playlists'),
	path('', include('django.contrib.auth.urls')),
]