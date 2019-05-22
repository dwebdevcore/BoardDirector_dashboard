from rest_framework import viewsets
from rest_framework.response import Response

from profiles.serializers import UserSerializer


class MeViewset(viewsets.ViewSet):
    def list(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)
