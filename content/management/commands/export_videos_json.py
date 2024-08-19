from django.core.management.base import BaseCommand
from content.admin import VideoResource
import json

class Command(BaseCommand):
    help = 'Exportiert alle Videos als JSON-Datei'

    def handle(self, *args, **kwargs):
        video_resource = VideoResource()
        dataset = video_resource.export()
        json_data = dataset.json

        # Speichern der JSON-Daten in einer Datei
        with open('videos_export.json', 'w') as json_file:
            json_file.write(json_data)
        
        self.stdout.write(self.style.SUCCESS('Videos erfolgreich exportiert als JSON.'))