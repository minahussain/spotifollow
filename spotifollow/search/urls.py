from django.urls import path
from django.conf.urls import include, url
from . import views

app_name = 'search'
urlpatterns = [
	path('search/<int:pk>', views.SearchDetailView.as_view(), name='search-detail'),
	path('search/', views.SearchListView.as_view(), name='search'),
	path('search/link', views.link_playlists, name='link-playlist'),
]