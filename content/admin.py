from django.contrib import admin
from import_export import resources
from content.models import Video
from import_export.admin import ImportExportModelAdmin


class VideoResource(resources.ModelResource):
    class Meta:
        model = Video  

class VideoAdmin(ImportExportModelAdmin):
    resource_classes = [VideoResource]


admin.site.register(Video, VideoAdmin)