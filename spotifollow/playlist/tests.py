from django.test import TestCase
from playlist.models import Track
from playlist.models import Playlist
from playlist.models import TrackInstance

class InitLinkedTrackStatusTest(TestCase):
	"""
	Tracks are initially added with status as Kept
	Once a playlist is linked, it will add Deleted tracks from the original playlist
	It will also change track status to Added for any added tracks from original playlist
	A refreshed playlist will also check for any newly Added tracks
	"""
	def setUp(self):
		self.track_a = Track.objects.create(track_id='1', title='A track', artist='Arty Art', artist_id='', href='')
		self.track_d = Track.objects.create(track_id='2', title='D track', artist='Darty Dart', artist_id='', href='')
		self.track_k = Track.objects.create(track_id='3', title='K track', artist='Karty Kart', artist_id='', href='')

		self.play_b = Playlist.objects.create(playlist_id='1', title='B playlist', author='Barty Bart', tracks_href='', href='')
		self.play_o = Playlist.objects.create(playlist_id='2', title='Orginal B playlist', author='Orty Ort', tracks_href='', href='')
		
		self.track_inst_k = TrackInstance.objects.create(playlist=self.play_b, track=self.track_k)
		self.track_inst_k2 = TrackInstance.objects.create(playlist=self.play_o, track=self.track_k)
		self.track_inst_d = TrackInstance.objects.create(playlist=self.play_o, track=self.track_d)
		self.track_inst_a = TrackInstance.objects.create(playlist=self.play_b, track=self.track_a)

		self.play_b.set_origin_playlist(self.play_o)

	def test_track_kept(self):
		self.assertTrue(self.track_inst_k.is_kept())
		self.assertTrue(self.track_inst_k2.is_kept())
		self.assertIn(self.track_k, self.play_b.tracks.all())
		kept_tracks = self.play_b.kept_tracks_set()
		self.assertIn(self.track_k, kept_tracks)
		self.assertEqual(1, self.play_b.kept_tracks_count())
		self.assertEqual(2, self.play_o.kept_tracks_count())

	def test_track_deleted(self):
		deleted_tracks = self.play_b.deleted_tracks_set()
		self.assertIn(self.track_d, deleted_tracks)
		track_inst_d2 = TrackInstance.objects.get(track=self.track_d, playlist=self.play_b)
		self.assertTrue(track_inst_d2.is_deleted())
		self.assertIn(self.track_d, self.play_b.tracks.all())
		self.assertIn(self.track_d, self.play_o.tracks.all())
		self.assertEqual(1, self.play_b.deleted_tracks_count())
		self.assertEqual(0, self.play_o.deleted_tracks_count())

	def test_track_added(self):
		added_tracks = self.play_b.added_tracks_set()
		self.assertIn(self.track_a, added_tracks)
		track_inst_a2 = TrackInstance.objects.get(track=self.track_a, playlist=self.play_b)
		self.assertTrue(track_inst_a2.is_added())
		self.assertIn(self.track_a, self.play_b.tracks.all())
		self.assertNotIn(self.track_a, self.play_o.tracks.all())
		self.assertEqual(1, self.play_b.added_tracks_count())
		self.assertEqual(0, self.play_o.added_tracks_count())

class ProcessTrackStatusTest(TestCase):
	"""
	Tracks are initially added with status as Kept
	Once a playlist is linked, it will add Deleted tracks from the original playlist
	It will also change track status to Added for any added tracks from original playlist
	A refreshed playlist will also check for any newly Added tracks
	"""
	def setUp(self):
		self.track_a = Track.objects.create(track_id='1', title='A track', artist='Arty Art', artist_id='', href='')
		self.track_d = Track.objects.create(track_id='2', title='D track', artist='Darty Dart', artist_id='', href='')
		self.track_k = Track.objects.create(track_id='3', title='K track', artist='Karty Kart', artist_id='', href='')

		self.play_b = Playlist.objects.create(playlist_id='1', title='B playlist', author='Barty Bart', tracks_href='', href='')
		self.play_o = Playlist.objects.create(playlist_id='2', title='Orginal B playlist', author='Orty Ort', tracks_href='', href='')
		self.play_t = Playlist.objects.create(playlist_id='3', title='Test playlist', author='Testy Test', tracks_href='', href='')
		
		self.track_inst_k = TrackInstance.objects.create(playlist=self.play_b, track=self.track_k)
		self.track_inst_k2 = TrackInstance.objects.create(playlist=self.play_o, track=self.track_k)
		self.track_inst_d = TrackInstance.objects.create(playlist=self.play_o, track=self.track_d)
		self.track_inst_a = TrackInstance.objects.create(playlist=self.play_b, track=self.track_a)
		self.track_inst_a2 = TrackInstance.objects.create(playlist=self.play_t, track=self.track_a)

		self.play_b.set_origin_playlist(self.play_o)

	def test_track_kept_to_deleted(self):
		self.play_b.delete_track(self.track_k)
		track_inst_k3 = TrackInstance.objects.get(track=self.track_k, playlist=self.play_b)
		self.assertTrue(track_inst_k3.is_deleted())

	def test_track_deleted_to_kept(self):
		self.play_b.add_track(self.track_k)
		self.play_b.add_track(self.track_d)
		track_inst_k4 = TrackInstance.objects.get(track=self.track_k, playlist=self.play_b)
		track_inst_d2 = TrackInstance.objects.get(track=self.track_d, playlist=self.play_b)
		self.assertTrue(track_inst_k4.is_kept())
		self.assertTrue(track_inst_d2.is_kept())

	def test_track_added_to_deleted(self):
		self.play_b.delete_track(self.track_a)
		added_tracks = self.play_b.added_tracks_set()
		self.assertNotIn(self.track_a, self.play_b.tracks.all())
		self.assertNotIn(self.track_a, added_tracks)
		test_tracks = self.play_t.tracks.all()
		self.assertIn(self.track_a, test_tracks)

class PlaylistTest(TestCase):
	"""
	Tracks are initially added with status as Kept
	Once a playlist is linked, it will add Deleted tracks from the original playlist
	It will also change track status to Added for any added tracks from original playlist
	A refreshed playlist will also check for any newly Added tracks
	"""
	def setUp(self):
		self.track_a = Track.objects.create(track_id='1', title='A track', artist='Arty Art', artist_id='', href='')
		self.track_d = Track.objects.create(track_id='2', title='D track', artist='Darty Dart', artist_id='', href='')
		self.track_k = Track.objects.create(track_id='3', title='K track', artist='Karty Kart', artist_id='', href='')

		self.play_b = Playlist.objects.create(playlist_id='1', title='B playlist', author='Barty Bart', tracks_href='', href='')
		self.play_o = Playlist.objects.create(playlist_id='2', title='Orginal B playlist', author='Orty Ort', tracks_href='', href='')
		self.play_t = Playlist.objects.create(playlist_id='3', title='Test playlist', author='Testy Test', tracks_href='', href='')
		
		self.track_inst_k = TrackInstance.objects.create(playlist=self.play_b, track=self.track_k)
		self.track_inst_k2 = TrackInstance.objects.create(playlist=self.play_o, track=self.track_k)
		self.track_inst_d = TrackInstance.objects.create(playlist=self.play_o, track=self.track_d)
		self.track_inst_a = TrackInstance.objects.create(playlist=self.play_b, track=self.track_a)
		self.track_inst_a2 = TrackInstance.objects.create(playlist=self.play_t, track=self.track_a)

		self.play_b.set_origin_playlist(self.play_o)

	def test_playlist_linked(self):
		self.assertTrue(self.play_b.is_linked())
		self.assertFalse(self.play_o.is_linked())
		self.assertTrue(self.play_b.origin_playlist == self.play_o)
		self.assertFalse(self.play_o.origin_playlist == self.play_b)

	def test_playlist_unlinked(self):
		self.play_b.unlink_list()
		self.assertFalse(self.play_b.is_linked())
		self.assertFalse(self.play_o.is_linked())
		self.assertFalse(self.play_b.origin_playlist == self.play_o)
		self.assertFalse(self.play_o.origin_playlist == self.play_b)
