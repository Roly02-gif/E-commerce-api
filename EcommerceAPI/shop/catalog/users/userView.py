from rest_framework.viewsets import ModelViewSet

from shop.catalog.users.userSerializer import UserSerializer
from shop.models import UserModel
from shop.permissions import IsOwnerOrAdmin


class UserViewSet(ModelViewSet):
    queryset = UserModel.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsOwnerOrAdmin]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return UserModel.objects.all()
        return UserModel.objects.filter(pk=user.pk)
