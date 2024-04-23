import os
import time
from datetime import datetime
from typing import Dict

from django.conf import settings
from os.path import isfile, join
from os import listdir

from django.core.files.uploadedfile import UploadedFile


class OcrFilesManager:
    def __init__(self, files: Dict[str, UploadedFile]):
        timestamp_files = {}
        gmt = time.gmtime()
        for file in files:
            new_file_name = str(gmt) + str(file)
            timestamp_files[new_file_name] = files[file]

        self.files = timestamp_files
        self.gmt = str(datetime.now().timestamp())
        self.result_file_url = settings.MEDIA_URL + '/' + str(self.gmt) + '/' + str('ocr-doc') + self.gmt + '.docx'
        self.dir_path = os.path.join(settings.MEDIA_ROOT, str(self.gmt))
        os.mkdir(self.dir_path)

    def get_result_file_url(self):
        return self.result_file_url

    def get_result_doc_name(self):
        return os.path.join(self.dir_path, str('ocr-doc') + self.gmt + '.docx')

    def get_secondary_images(self):
        return self._get_primary_files()

    def get_secondary_image_name(self, image_index):
        return join(self.dir_path, str(image_index) + ".jpg")

    def _get_primary_files(self):
        files = [join(self.dir_path, f) for f in listdir(self.dir_path) if
                 isfile(join(self.dir_path, f))]
        return files

    @staticmethod
    def is_pdf(file_name):
        return str.endswith(file_name, '.pdf')
