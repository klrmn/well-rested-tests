from django.contrib.auth.models import User
from rest_framework import routers, serializers, viewsets
from attachment import ImageViewSet, TextViewSet
from case import CaseViewSet
from run import RunViewSet
from case_run import CaseRunViewSet
from project import ProjectViewSet
from run import RunSerializer
from run_env_var import RunEnvVarViewSet


# Serializers define the API representation.
class UserSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = User
        fields = ('url', 'username', 'email', 'is_staff')

# ViewSets define the view behavior.
class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer


# Routers provide an easy way of automatically determining the URL conf.
router = routers.DefaultRouter()
router.register(r'api/users', UserViewSet)
router.register(r'api/projects', ProjectViewSet)
router.register(r'api/screenshots', ImageViewSet)
router.register(r'api/logs', TextViewSet)
router.register(r'api/cases', CaseViewSet)
router.register(r'api/environments', RunEnvVarViewSet)
router.register(r'api/case_runs', CaseRunViewSet)
router.register(r'api/runs', RunViewSet)
