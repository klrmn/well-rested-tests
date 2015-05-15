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
router.register(r'api/users', UserViewSet)
router.register(r'api/projects', ProjectViewSet)
router.register(r'api/screenshots', ImageViewSet)
router.register(r'api/logs', TextViewSet)
router.register(r'api/cases', CaseViewSet)
router.register(r'api/tags', TagViewSet)
router.register(r'api/results', ResultViewSet)
router.register(r'api/runs', RunViewSet)
