from django.conf.urls import include, url
from django.contrib import admin
from wrt.rest_router import router


urlpatterns = [
    # Examples:
    # url(r'^$', 'wrt.views.home', name='home'),
    # url(r'^blog/', include('blog.urls')),
    url(r'^', include(router.urls)),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework')),
]
