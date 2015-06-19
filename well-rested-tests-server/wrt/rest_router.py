from rest_framework import routers, serializers, viewsets
from attachment import ImageViewSet, TextViewSet
from user import UserViewSet
from case import CaseViewSet
from run import RunViewSet
from result import ResultViewSet
from project import ProjectViewSet
from run import RunSerializer
from tag import TagViewSet


# Routers provide an easy way of automatically determining the URL conf.
router = routers.DefaultRouter()
router.register(r'users', UserViewSet)
router.register(r'logs', TextViewSet)
router.register(r'cases', CaseViewSet)
router.register(r'tags', TagViewSet)
router.register(r'results', ResultViewSet)
router.register(r'runs', RunViewSet)
