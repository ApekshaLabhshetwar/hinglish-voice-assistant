import uuid
from django.conf import settings
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser
from .serializers import VoiceUploadSerializer
from .tasks import process_audio_task


class VoiceAPIView(GenericAPIView):
    serializer_class = VoiceUploadSerializer
    parser_classes = [MultiPartParser]

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        file = serializer.validated_data["file"]

        record_id = str(uuid.uuid4())
        input_path = settings.MEDIA_ROOT / f"{record_id}_{file.name}"

        with open(input_path, "wb") as f:
            for chunk in file.chunks():
                f.write(chunk)

        # 🔥 CELERY TASK TRIGGER
        process_audio_task.delay(str(input_path), record_id)

        return Response({
            "message": "Audio received. Processing started in background.",
            "task_id": record_id,
        })
