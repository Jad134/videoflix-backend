import subprocess 
import os
from content.models import Video
from django.core.files import File

def convert_480p(source, video_id):
    os.environ['PATH'] += r';C:\Dev\tools\ffmpeg\ffmpeg-master-latest-win64-gpl\ffmpeg-master-latest-win64-gpl\bin'
    base, ext = os.path.splitext(source)
    target = f"{base}_480p{ext}"
    cmd = r'C:\Dev\tools\ffmpeg\ffmpeg-master-latest-win64-gpl\ffmpeg-master-latest-win64-gpl\bin\ffmpeg -i "{}" -s hd480 -c:v libx264 -crf 23 -c:a aac -strict -2 "{}"'.format(source, target)
    subprocess.run(cmd, shell=True, check=True)
    update_converted_files(video_id)

def convert_720p(source, video_id):
    os.environ['PATH'] += r';C:\Dev\tools\ffmpeg\ffmpeg-master-latest-win64-gpl\ffmpeg-master-latest-win64-gpl\bin'
    base, ext = os.path.splitext(source)
    target = f"{base}_720p{ext}"
    cmd = r'C:\Dev\tools\ffmpeg\ffmpeg-master-latest-win64-gpl\ffmpeg-master-latest-win64-gpl\bin\ffmpeg -i "{}" -s  hd720 -c:v libx264 -crf 23 -c:a aac -strict -2 "{}"'.format(source, target)
    subprocess.run(cmd, shell=True, check=True)
    update_converted_files(video_id)

 
def update_converted_files(video_id):
    video = Video.objects.get(id=video_id)
    base, ext = os.path.splitext(video.video_file.path)

    # Überprüfen und Aktualisieren der 480p-Version
    video_480p_path = f"{base}_480p{ext}"
    if os.path.exists(video_480p_path) and not video.video_480p:
        with open(video_480p_path, 'rb') as f:
            video.video_480p.save(f"{video.title}_480p{ext}", File(f))
    
    # Überprüfen und Aktualisieren der 720p-Version
    video_720p_path = f"{base}_720p{ext}"
    if os.path.exists(video_720p_path) and not video.video_720p:
        with open(video_720p_path, 'rb') as f:
            video.video_720p.save(f"{video.title}_720p{ext}", File(f))

    video.save()