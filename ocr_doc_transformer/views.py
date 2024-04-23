from rest_framework.views import APIView
from rest_framework.response import Response

from .classes.ocr_creator import OcrCreator
from .serializers import FileSerializer
from rest_framework import status
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser


class FilesAPIView(APIView):
    parser_classes = (MultiPartParser, FormParser, JSONParser)
    serializer_class = FileSerializer

    def post(self, request):
        files_list = request.FILES

        ocr_creator = OcrCreator(files_list)
        result_doc_url = ocr_creator.create_document()

        return Response({'resultFile': result_doc_url}, status=status.HTTP_201_CREATED)
