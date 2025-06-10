from django.urls import path
from .views import (
    api_sign_up,
    activate_user,
    api_logout,
    api_forgot_password,
    api_reset_password,
    CustomTokenObtainPairView,  # استيراد الكلاس الجديد
)

urlpatterns = [
    path('signup/', api_sign_up, name='api_sign_up'),
    path('login/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),  
    path('activate/<uidb64>/<token>/', activate_user, name='activate_user'),
    path('logout/', api_logout, name='api_logout'),
    path('forgot-password/', api_forgot_password, name='api_forgot_password'),
    path('reset-password/', api_reset_password, name='api_reset_password'),
]
