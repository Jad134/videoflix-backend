from datetime import date
from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
import os
from content.models import Video

class VideoModelTest(TestCase):
    def setUp(self):
        self.video_file = SimpleUploadedFile("test_video.mp4", b"file_content", content_type="video/mp4")
        self.video = Video.objects.create(
            title='Test Video',
            description='A test video description.',
            video_file=self.video_file,
            category='Test Category'
        )

    def test_video_str_method(self):
        self.assertEqual(str(self.video), 'Test Video')

    def test_video_default_created_at(self):
        self.assertEqual(self.video.created_at, date.today())

    def test_video_field_max_lengths(self):
        video = Video.objects.get(id=self.video.id)
        max_length_title = video._meta.get_field('title').max_length
        max_length_description = video._meta.get_field('description').max_length
        max_length_category = video._meta.get_field('category').max_length

        self.assertEqual(max_length_title, 80)
        self.assertEqual(max_length_description, 500)
        self.assertEqual(max_length_category, 40)

    def test_video_file_field_options(self):
        video = Video.objects.get(id=self.video.id)
        video_file_field = video._meta.get_field('video_file')
        video_480p_field = video._meta.get_field('video_480p')
        video_720p_field = video._meta.get_field('video_720p')

        self.assertTrue(video_file_field.blank)
        self.assertTrue(video_file_field.null)
        self.assertTrue(video_480p_field.blank)
        self.assertTrue(video_480p_field.null)
        self.assertTrue(video_720p_field.blank)
        self.assertTrue(video_720p_field.null)

    def test_video_file_upload(self):
    # Extrahiere nur den Basisnamen der Datei
     uploaded_file_name = os.path.basename(self.video.video_file.name)
     self.assertTrue(uploaded_file_name.startswith('test_video'))
     self.assertTrue(uploaded_file_name.endswith('.mp4'))


   
