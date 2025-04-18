import subprocess 
import os
from content.models import Video
from django.core.files import File



def convert_video(source, video_id, resolution):
    print("Current PATH:", os.environ['PATH'])
    os.environ['PATH'] += r';D:\Dev\tools\ffmpeg-2025-04-17-git-7684243fbe-full_build\bin'
    base, ext = os.path.splitext(source)
    target = f"{base}_{resolution}p{ext}"
    if resolution == 480:
       cmd = r'"D:\Dev\tools\ffmpeg-2025-04-17-git-7684243fbe-full_build\bin\ffmpeg.exe" -i "{}" -s hd480 -c:v libx264 -crf 23 -c:a aac -strict -2 "{}"'.format(source, target)
    elif resolution == 720:
       cmd = r'"D:\Dev\tools\ffmpeg-2025-04-17-git-7684243fbe-full_build\bin\ffmpeg.exe" -i "{}" -s hd720 -c:v libx264 -crf 23 -c:a aac -strict -2 "{}"'.format(source, target)
    subprocess.run(cmd, shell=True, check=True)
    update_converted_files(video_id)

 
def update_converted_files(video_id):
    video = Video.objects.get(id=video_id)
    base, ext = os.path.splitext(video.video_file.path)


    video_480p_path = f"{base}_480p{ext}"
    if os.path.exists(video_480p_path) and not video.video_480p:
        with open(video_480p_path, 'rb') as f:
            video.video_480p.save(f"{video.title}_480p{ext}", File(f))
    

    video_720p_path = f"{base}_720p{ext}"
    if os.path.exists(video_720p_path) and not video.video_720p:
        with open(video_720p_path, 'rb') as f:
            video.video_720p.save(f"{video.title}_720p{ext}", File(f))

    video.save()