from django.db import models
from storages.backends.s3boto3 import S3Boto3Storage


class ClientDocsStorage(S3Boto3Storage):
    bucket_name = 'ocr-bucket'
    file_overwrite = False


class File(models.Model):
    file = models.FileField()
    upload = models.FileField(storage=ClientDocsStorage())
    uploaded_on = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.uploaded_on.date()
