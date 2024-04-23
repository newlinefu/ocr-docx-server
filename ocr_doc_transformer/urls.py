from django.urls import path
from .views import FilesAPIView

app_name = 'ocr-doc-transformer'

urlpatterns = [
    path('upload-file/', FilesAPIView.as_view(), name='upload-file'),
]
