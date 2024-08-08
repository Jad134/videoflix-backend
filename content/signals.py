import os
from django.dispatch import receiver
from content.models import Video
from django.db.models.signals import post_save, post_delete

@receiver(post_save, sender = Video)
def video_post_save(sender, instance, created, **kwargs):
    print('Video wurde gepeichert')
    if created: 
        print('New Video created')


@receiver(post_delete, sender = Video)
def video_post_delete(sender, instance,  **kwargs):
    """
    Deletes file from filesystem
    when corresponding `MediaFile` object is deleted.
    """
    if instance.video_file:
        if os.path.isfile(instance.video_file.path):
            os.remove(instance.video_file.path)

