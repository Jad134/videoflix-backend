import subprocess 
import os


def convert_480p(source):
 os.environ['PATH'] += r';C:\Dev\tools\ffmpeg\ffmpeg-master-latest-win64-gpl\ffmpeg-master-latest-win64-gpl\bin'
 base, ext = os.path.splitext(source)
 target = f"{base}_480p{ext}"
 cmd = r'C:\Dev\tools\ffmpeg\ffmpeg-master-latest-win64-gpl\ffmpeg-master-latest-win64-gpl\bin\ffmpeg -i "{}" -s hd480 -c:v libx264 -crf 23 -c:a aac -strict -2 "{}"'.format(source, target)
 subprocess.run(cmd, shell=True, check=True)


def convert_720p(source):
 os.environ['PATH'] += r';C:\Dev\tools\ffmpeg\ffmpeg-master-latest-win64-gpl\ffmpeg-master-latest-win64-gpl\bin'
 base, ext = os.path.splitext(source)
 target = f"{base}_720p{ext}"
 cmd = r'C:\Dev\tools\ffmpeg\ffmpeg-master-latest-win64-gpl\ffmpeg-master-latest-win64-gpl\bin\ffmpeg -i "{}" -s  hd720 -c:v libx264 -crf 23 -c:a aac -strict -2 "{}"'.format(source, target)
 subprocess.run(cmd, shell=True, check=True)

 