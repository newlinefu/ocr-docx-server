from typing import Dict
import numpy as np
import pytesseract
from django.core.files.uploadedfile import UploadedFile
from docx import Document
from pdf2image import convert_from_bytes
from PIL import Image

from ocr_doc_transformer.classes.document_part import CreatedDocumentPart
from ocr_doc_transformer.classes.ocr_files_manager import OcrFilesManager


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
        document_structure = self.get_doc_structure_from_files()
        for part in document_structure:
            if part.part_type == "paragraph":
                document.add_paragraph(part.content)
            elif part.part_type == "pageBreak":
                document.add_page_break()

        return document

    def create_document(self):
        document = self.create_document_object()
        result_doc_name = self.files_manager.get_result_doc_name()
        result_doc_url = self.files_manager.get_result_file_url()
        document.save(result_doc_name)
        return result_doc_url

    @staticmethod
    def get_doc_structure_from_image(file: UploadedFile):
        img = np.array(Image.open(file))
        text = pytesseract.image_to_string(img, lang='rus')
        return [
            CreatedDocumentPart("paragraph", text),
            CreatedDocumentPart("pageBreak")
        ]
