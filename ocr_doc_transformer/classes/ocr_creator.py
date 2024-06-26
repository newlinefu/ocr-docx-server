import os
from io import BytesIO
from typing import Dict, List

import boto3
import numpy as np
import pytesseract
from django.core.files.uploadedfile import UploadedFile
from docx import Document
from pdf2image import convert_from_bytes
from PIL import Image
from pytesseract import Output

from ocr_doc_transformer.classes.document_elements.table.table import Table
from ocr_doc_transformer.classes.ocr_files_manager import OcrFilesManager
from ocr_doc_transformer.classes.page_structure import PageStructure
from django.conf import settings


class OcrCreator:
    def __init__(self, files: Dict[str, UploadedFile]):
        self.files = files
        self.files_manager = OcrFilesManager(files)

    def get_doc_structure_from_pdf(self, file):
        pages = convert_from_bytes(file.read(), 500)
        image_counter = 1

        for page in pages:
            filename = self.files_manager.get_secondary_image_name(image_counter)
            page.save(filename, 'JPEG')
            image_counter = image_counter + 1

        secondary_images = self.files_manager.get_secondary_images()
        doc_structure = []

        for secondary_image in secondary_images:
            structure_part = self.get_doc_structure_from_image(secondary_image)

            for j in range(len(structure_part)):
                doc_structure.append(structure_part[j])

        return doc_structure

    def get_doc_structure_from_files(self):
        result_structure = []
        for file_name in self.files:
            single_structure = []
            file = self.files[file_name]
            if OcrFilesManager.is_pdf(file.name):
                single_structure = self.get_doc_structure_from_pdf(file)
            else:
                single_structure = OcrCreator.get_doc_structure_from_image(file)
            for part in single_structure:
                result_structure.append(part)

        return result_structure

    def create_document_object(self):
        document = Document()
        document_structure: List[PageStructure] = self.get_doc_structure_from_files()
        for part in document_structure:
            part.add_to(document)

        return document

    def create_document(self):
        document = self.create_document_object()
        result_doc_name = self.files_manager.get_result_short_name()
        result_doc_url = self.files_manager.get_result_file_url()
        session = boto3.session.Session()
        s3 = session.client(
            service_name='s3',
            endpoint_url=settings.AWS_S3_ENDPOINT_URL,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        )
        with BytesIO() as file_obj:
            document.save(file_obj)
            file_obj.seek(0)
            s3.upload_fileobj(file_obj, os.environ.get('S3_BUCKET_NAME'), result_doc_name)

        return settings.AWS_S3_ENDPOINT_URL + '/' + os.environ.get('S3_BUCKET_NAME') + '/' + result_doc_name

    @staticmethod
    def get_doc_structure_from_image(file: UploadedFile):
        img = np.array(Image.open(file))
        tables = Table.get_tables_from_image(file)
        image_data = pytesseract.image_to_data(img, lang="eng+rus", output_type=Output.DICT)
        page_structure = PageStructure(image_data, tables)

        return [page_structure]
