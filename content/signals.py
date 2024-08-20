import os
from django.dispatch import receiver
from content.models import Video
from django.db.models.signals import post_save, post_delete
from content.tasks import convert_480p, convert_720p
import django_rq
from django.core.files import File

@receiver(post_save, sender=Video)
def video_post_save(sender, instance, created, **kwargs):
    print('Video wurde gepeichert')
    if created: 
        print('New Video created')
        queue = django_rq.get_queue('default', autocommit=True)
        # Enqueue conversion tasks with video_id
        queue.enqueue(convert_480p, instance.video_file.path, instance.id)
        queue.enqueue(convert_720p, instance.video_file.path, instance.id)


@receiver(post_delete, sender = Video)
def video_post_delete(sender, instance,  **kwargs):
    """
    Deletes file from filesystem
    when corresponding `MediaFile` object is deleted.
    """
    if instance.video_file:
        if os.path.isfile(instance.video_file.path):
            os.remove(instance.video_file.path)



@receiver(post_save, sender=Video)
def update_converted_files(sender, instance, **kwargs):
    base, ext = os.path.splitext(instance.video_file.path)

    # Überprüfen und Aktualisieren der 480p-Version
    video_480p_path = f"{base}_480p{ext}"
    if os.path.exists(video_480p_path) and not instance.video_480p:
        with open(video_480p_path, 'rb') as f:
            instance.video_480p.save(f"{instance.title}_480p{ext}", File(f))
        instance.save()

    # Überprüfen und Aktualisieren der 720p-Version
    video_720p_path = f"{base}_720p{ext}"
    if os.path.exists(video_720p_path) and not instance.video_720p:
        with open(video_720p_path, 'rb') as f:
            instance.video_720p.save(f"{instance.title}_720p{ext}", File(f))
        instance.save()
