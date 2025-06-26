from rest_framework import viewsets, status, serializers
from .models import CustomUser, ChargingStation, Reservation
from .serializers import UserSerializer, StationSerializer, ReservationSerializer, CustomTokenObtainPairSerializer
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAdminUser
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.decorators import api_view, permission_classes
from django.utils import timezone
from datetime import timedelta
import re
from .utils import is_station_reserved


# ✅ VALIDARE CNP
def is_valid_cnp(cnp, birth_date):
    if not re.match(r'^\d{13}$', cnp):
        return False

    control = '279146358279'
    suma = sum(int(cnp[i]) * int(control[i]) for i in range(12))
    rest = suma % 11
    cifra_control = 1 if rest == 10 else rest
    if cifra_control != int(cnp[-1]):
        return False

    try:
        yy = int(cnp[1:3])
        mm = int(cnp[3:5])
        dd = int(cnp[5:7])
        s = int(cnp[0])

        if s in [1, 2]:
            year = 1900 + yy
        elif s in [5, 6]:
            year = 2000 + yy
        else:
            return False

        from datetime import datetime
        cnp_date = datetime(year, mm, dd).date()
        return str(cnp_date) == birth_date
    except:
        return False


class UserViewSet(viewsets.ModelViewSet):
    queryset = CustomUser.objects.all()
    serializer_class = UserSerializer


class StationViewSet(viewsets.ModelViewSet):
    queryset = ChargingStation.objects.all()
    serializer_class = StationSerializer
    permission_classes = [AllowAny]


class ReservationViewSet(viewsets.ModelViewSet):
    queryset = Reservation.objects.all()
    serializer_class = ReservationSerializer
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        user = request.user
        now = timezone.now()

        has_validated_active = Reservation.objects.filter(
            user=user,
            is_validated=True,
            is_cancelled=False,
            start_time__lte=now,
            end_time__gte=now
        ).exists()

        if has_validated_active:
            return Response(
                {"error": "⚠️ Ai deja o rezervare validată activă. Poți avea o singură rezervare activă odată."},
                status=status.HTTP_400_BAD_REQUEST
            )

        existing_pending = Reservation.objects.filter(
            user=user,
            is_validated=False,
            is_cancelled=False,
            start_time__gte=now - timedelta(minutes=30)
        ).first()

        if existing_pending:
            return Response(
                {"error": "⚠️ Ai deja o rezervare în așteptare. Valideaz-o, anuleaz-o sau așteaptă expirarea acesteia."},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        start_time = serializer.validated_data['start_time']
        end_time = start_time + timedelta(hours=1)

        reservation = serializer.save(user=user, end_time=end_time)

        station = reservation.station
        station.available = False
        station.save()

        return Response(serializer.data, status=status.HTTP_201_CREATED)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_reservations(request):
    reservations = Reservation.objects.filter(
        user=request.user,
        is_hidden_by_user=False
    ).order_by('-start_time').select_related('station')

    serializer = ReservationSerializer(reservations, many=True)
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def validate_reservation(request, reservation_id):
    try:
        reservation = Reservation.objects.get(id=reservation_id, user=request.user)

        if reservation.is_validated:
            return Response({'error': 'Rezervarea este deja validată.'}, status=400)

        reservation.is_validated = True
        reservation.end_time = reservation.start_time + timedelta(hours=1)
        reservation.station.available = False
        reservation.station.save()
        reservation.save()

        return Response({'success': 'Rezervarea a fost validată și stația este acum ocupată.'})
    except Reservation.DoesNotExist:
        return Response({'error': 'Rezervarea nu a fost găsită.'}, status=404)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def cancel_reservation(request, reservation_id):
    try:
        reservation = Reservation.objects.get(id=reservation_id, user=request.user)
        if reservation.is_validated:
            return Response({'error': 'Rezervarea a fost deja validată și nu poate fi anulată.'}, status=400)
        reservation.is_cancelled = True
        reservation.save()
        return Response({'success': 'Rezervarea a fost anulată de către dumneavoastră.'})
    except Reservation.DoesNotExist:
        return Response({'error': 'Rezervarea nu a fost găsită.'}, status=status.HTTP_404_NOT_FOUND)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_profile(request):
    user = request.user
    data = {
        "username": user.username,
        "email": user.email,
        "phone": user.phone if hasattr(user, 'phone') else '',
        "full_name": f"{user.first_name} {user.last_name}".strip()
    }
    return Response(data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def hide_reservation(request, reservation_id):
    try:
        reservation = Reservation.objects.get(id=reservation_id, user=request.user)
        reservation.is_hidden_by_user = True
        reservation.save()
        return Response({'success': 'Rezervarea a fost ascunsă din profil.'})
    except Reservation.DoesNotExist:
        return Response({'error': 'Rezervarea nu a fost găsită.'}, status=404)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def hidden_reservations(request):
    reservations = Reservation.objects.filter(
        user=request.user,
        is_hidden_by_user=True
    ).order_by('-start_time').select_related('station')

    serializer = ReservationSerializer(reservations, many=True)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([AllowAny])
def stations_with_status(request):
    stations = ChargingStation.objects.all()
    now = timezone.now()

    data = []
    for station in stations:
        has_active_reservation = Reservation.objects.filter(
            station=station,
            is_validated=True,
            is_cancelled=False,
            start_time__lte=now,
            end_time__gte=now
        ).exists()

        if not has_active_reservation and not station.available:
            station.available = True
            station.save()
        elif has_active_reservation and station.available:
            station.available = False
            station.save()

        data.append({
            'id': station.id,
            'name': station.name,
            'city': station.city,
            'lat': station.lat,
            'lon': station.lon,
            'is_reserved': has_active_reservation,
            'connector_type': station.connector_type,
            'power_kw': station.power_kw,
            'price_per_kwh': station.price_per_kwh
        })

    return Response(data)


@api_view(['GET'])
@permission_classes([IsAdminUser])
def admin_dashboard_summary(request):
    now = timezone.now()

    total_users = CustomUser.objects.count()
    total_stations = ChargingStation.objects.count()
    total_reservations = Reservation.objects.count()
    active_reservations = Reservation.objects.filter(
        is_validated=True,
        is_cancelled=False,
        start_time__lte=now,
        end_time__gte=now
    ).count()

    from django.db.models import Count
    top_stations = Reservation.objects.values('station__name') \
        .annotate(count=Count('id')) \
        .order_by('-count')[:5]

    top_stations_list = [{'name': s['station__name'], 'count': s['count']} for s in top_stations]

    return Response({
        "totalUsers": total_users,
        "totalStations": total_stations,
        "totalReservations": total_reservations,
        "activeReservations": active_reservations,
        "topStations": top_stations_list
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def all_users(request):
    if not request.user.is_staff:
        return Response({'error': 'Nu ai acces la această resursă.'}, status=403)

    users = CustomUser.objects.all().order_by('-date_joined')
    data = [{
        'id': u.id,
        'username': u.username,
        'email': u.email,
        'is_staff': u.is_staff,
        'date_joined': u.date_joined,
    } for u in users]

    return Response(data)


@api_view(['GET'])
@permission_classes([IsAdminUser])
def all_reservations(request):
    reservations = Reservation.objects.select_related('user', 'station').all().order_by('-start_time')

    data = [{
        'id': r.id,
        'username': r.user.username,
        'station': r.station.name,
        'start_time': r.start_time,
        'end_time': r.end_time,
        'is_validated': r.is_validated,
        'is_cancelled': r.is_cancelled
    } for r in reservations]

    return Response(data)


class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        data = request.data

        if CustomUser.objects.filter(username=data.get('username')).exists():
            return Response({'error': 'Username already exists'}, status=status.HTTP_400_BAD_REQUEST)
        if CustomUser.objects.filter(email=data.get('email')).exists():
            return Response({'error': 'Email already exists'}, status=status.HTTP_400_BAD_REQUEST)

        email = data.get('email')
        if not re.match(r"^[\w\.-]+@(gmail\.com|yahoo\.com)$", email):
            return Response({'error': 'Email must be gmail.com or yahoo.com'}, status=status.HTTP_400_BAD_REQUEST)

        phone = data.get('phone')
        if not re.match(r"^(\+40|07)\d{8}$", phone):
            return Response({'error': 'Telefon invalid. Trebuie să înceapă cu +40 sau 07 și să aibă 10 cifre.'}, status=status.HTTP_400_BAD_REQUEST)

        cnp = data.get('cnp')
        birth_date = data.get('birth_date')

        if not is_valid_cnp(cnp, birth_date):
            return Response({'error': 'CNP invalid sau nu corespunde cu data de naștere'}, status=status.HTTP_400_BAD_REQUEST)

        user = CustomUser.objects.create_user(
            username=data.get('username'),
            password=data.get('password'),
            email=email,
            first_name=data.get('first_name'),
            last_name=data.get('last_name'),
            phone=phone,
            birth_date=birth_date,
            cnp=cnp
        )
        user.is_active = True
        user.save()

        return Response({'message': 'Cont creat cu succes!'}, status=status.HTTP_201_CREATED)


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer
