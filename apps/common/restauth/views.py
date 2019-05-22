from rest_framework import viewsets
from rest_framework.authentication import get_authorization_header
from rest_framework.authtoken.serializers import AuthTokenSerializer
from rest_framework.decorators import list_route
from rest_framework.response import Response
from rest_framework.status import HTTP_405_METHOD_NOT_ALLOWED, HTTP_201_CREATED, HTTP_403_FORBIDDEN

from common.models import AuthToken
from common.serializers import TokenSerializer


class TokenAuthViewset(viewsets.ViewSet):
    """
    Viewset to authenticate by token:

    - `POST /api/v1/token-auth/` to get new token. Data: `{"username": "some@email.here", "password": "and-password-also"}`. Response will contain `token` field and user details.
    - `POST /api/v1/token-auth/logout/` to logout current token

    Supplied token must be passed via `Authorization: token ${token}` header to all subsequent requests (Like `Authorization: token 123dasd123s1`).

    Please note that tokens have limited lifetime (30 days by default). So user must login again after this time.
    """
    serializer_class = AuthTokenSerializer

    def list(self, request):
        return Response("Use POST to login.", status=HTTP_405_METHOD_NOT_ALLOWED)

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']

        token = AuthToken.objects.create(user=user)

        token_serializer = TokenSerializer(token)

        return Response(token_serializer.data, status=HTTP_201_CREATED)

    @list_route(methods=['POST'])
    def logout(self, request):
        auth = get_authorization_header(request).split()
        if not auth or len(auth) != 2 or auth[0].lower() != 'token':
            return Response("Can't logout token without correct token auth headers", status=HTTP_403_FORBIDDEN)

        try:
            token = AuthToken.objects.get(token=auth[1])
        except AuthToken.DoesNotExist:
            return Response("Incorrect token")

        token.disabled = True
        token.save()

        return Response("Logout")
