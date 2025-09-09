"""
URL configuration for ita_project project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from views import db_connectivity,register_user_postgres,login_with_code,protected_view,create_recruitment_request,create_employee,create_leave_request,assign_missions
from django.urls import path, include
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

urlpatterns = [
    path('admin/', admin.site.urls),
    path("db-health/", db_connectivity, name="db_health"),
    #path("run-query/", run_select_query, name="run_query"),
    #path("get-users/", get_users_query, name="get_users"),
    #path("query/<str:query_name>/", run_predefined_query, name="run_predefined_query"),
    #path("register/", register_user, name="register_user"),
    #path("register-new-user/", register_new_user, name="register_user"),
    path("register-pg/", register_user_postgres, name="register_user_postgres"),
    #path("login/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    #path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("login/", login_with_code, name="login"),   # ✅ login custom
    path("login-protected/", protected_view, name="protected_view"),   # ✅ login custom
    #path("me/", me, name="me"),
    path("recruitment/create/", assign_missions, name="assign_missions"),
    path("employee/create/", create_employee, name="create_employee"),
    path("leave/create/", create_leave_request, name="create_leave_request"),
    path("recruitment/create/", create_recruitment_request, name="create_recruitment_request"),

]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
