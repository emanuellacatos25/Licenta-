import core.views  # 👈 Forțăm executarea views.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import UserViewSet, StationViewSet, ReservationViewSet, RegisterView, CustomTokenObtainPairView, user_reservations, validate_reservation, cancel_reservation, user_profile, hide_reservation, hidden_reservations,stations_with_status, admin_dashboard_summary, all_users, all_reservations
from rest_framework_simplejwt.views import TokenRefreshView
from core.views import CustomTokenObtainPairView, stations_with_status , admin_dashboard_summary,all_reservations
from django.urls import path



router = DefaultRouter()
router.register(r'users', UserViewSet)
router.register(r'stations', StationViewSet)
router.register(r'reservations', ReservationViewSet)

urlpatterns = [
    path('stations/with_status/', stations_with_status, name='stations_with_status'),  # 👈 acest rând trebuie să fie primul

    path('', include(router.urls)),
    path('token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('register/', RegisterView.as_view(), name='register'),
    path('my-reservations/', user_reservations, name='user_reservations'),
    path('validate-reservation/<int:reservation_id>/', validate_reservation, name='validate_reservation'),
    path('cancel-reservation/<int:reservation_id>/', cancel_reservation, name='cancel_reservation'),
    path('user-profile/', user_profile, name='user-profile'),
    path('hide-reservation/<int:reservation_id>/', hide_reservation, name='hide_reservation'),
    path('hidden-reservations/', hidden_reservations, name='hidden_reservations'),
    path('admin-dashboard/', admin_dashboard_summary, name='admin-dashboard'),
    path('admin/users/', all_users, name='admin-users'),
    path('admin/reservations/', all_reservations, name='admin-reservations'),


]


