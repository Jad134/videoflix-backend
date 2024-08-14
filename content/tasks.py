import subprocess 



def convert_480p(source):
 target = source + '_480p.mp4'
 cmd = 'ffmpeg -i "{}" -s hd480 -c:v libx264 -crf 23 -c:a aac -strict -2 "{}"'.format(source, target)
 print(f"Auszuführender Befehl: {cmd}")
 subprocess.run(cmd)