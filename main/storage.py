import os
from django.conf import settings
from django.core.files.storage import FileSystemStorage
from storages.backends.s3boto3 import S3Boto3Storage


class HybridS3Storage(S3Boto3Storage):
    """S3 storage that falls back to local filesystem for existing files."""

    def url(self, name):
        local = FileSystemStorage()
        local_path = os.path.join(settings.MEDIA_ROOT, name)
        if os.path.exists(local_path):
            return local.url(name)
        return super().url(name)
