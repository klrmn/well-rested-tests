from django.conf.urls import include, url
from django.contrib import admin
from wrt.rest_router import router
from wrt import views


urlpatterns = [
    # Examples:
    # url(r'^$', 'wrt.views.home', name='home'),
    # url(r'^blog/', include('blog.urls')),
    url(r'^api/', include(router.urls)),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    url(r'^', include(views)),
]
