from rest_framework import generics, permissions
from rest_framework import filters as drf_filters
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework_simplejwt.views import TokenObtainPairView

from authentication_app.models import User
from prescription.models import Prescription
from medicine.models import Medicine
from .serializers import (
    UserSerializer,
    MedicalRecordSerializer,
    PrescriptionSerializer,
    MedicineDetailSerializer,
    MedicineListSerializer,
    PharmacyAvailabilitySerializer,
)


class ObtainTokenPairView(TokenObtainPairView):
    """Uses Simple JWT's token view; left for URL wiring."""
    pass


class PatientProfileView(generics.RetrieveAPIView):
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user


class MedicalRecordView(generics.RetrieveAPIView):
    serializer_class = MedicalRecordSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return getattr(self.request.user, 'medical_record', None)


class PrescriptionListView(generics.ListAPIView):
    serializer_class = PrescriptionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_patient:
            return Prescription.objects.filter(patient=user).order_by('-prescribed_date')
        # allow doctors to view prescriptions they authored
        if user.is_doctor:
            return Prescription.objects.filter(doctor=user).order_by('-prescribed_date')
        return Prescription.objects.none()


class PrescriptionDetailView(generics.RetrieveAPIView):
    serializer_class = PrescriptionSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = Prescription.objects.all()


class MedicineDetailView(generics.RetrieveAPIView):
    serializer_class = MedicineDetailSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = Medicine.objects.filter(is_active=True)


class MedicineListView(generics.ListAPIView):
    serializer_class = MedicineListSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = Medicine.objects.filter(is_active=True)
    # enable search on name and generic_name and ordering
    filter_backends = [drf_filters.SearchFilter, drf_filters.OrderingFilter]
    search_fields = ['name', 'generic_name', 'strength']
    ordering_fields = ['name', 'created_at']


class MedicineAvailabilityView(generics.ListAPIView):
    """Return pharmacies (pharmacists) with stock for a medicine id.
    Query params: ?lat=&lng=&radius_km= optional for filtering by proximity.
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = PharmacyAvailabilitySerializer

    def get(self, request, pk):
        from inventory.models import PharmacyInventory
        import math

        def haversine(lat1, lon1, lat2, lon2):
            # all args expected as floats or Decimals; returns distance in km
            R = 6371.0
            phi1 = math.radians(float(lat1))
            phi2 = math.radians(float(lat2))
            dphi = math.radians(float(lat2) - float(lat1))
            dlambda = math.radians(float(lon2) - float(lon1))
            a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
            return 2 * R * math.asin(math.sqrt(a))

        lat = request.query_params.get('lat')
        lng = request.query_params.get('lng')
        radius_km = request.query_params.get('radius_km')
        try:
            lat = float(lat) if lat is not None else None
            lng = float(lng) if lng is not None else None
            radius_km = float(radius_km) if radius_km is not None else None
        except (ValueError, TypeError):
            lat = lng = radius_km = None

        qs = PharmacyInventory.objects.filter(batch__medicine_id=pk, current_stock__gt=0).select_related('pharmacist', 'batch')
        results = []
        for inv in qs:
            pharmacist = getattr(inv, 'pharmacist', None)
            profile = getattr(pharmacist, 'pharmacist_profile', None)
            plat = profile.latitude if profile and profile.latitude is not None else None
            plng = profile.longitude if profile and profile.longitude is not None else None
            distance = None
            if lat is not None and lng is not None and plat is not None and plng is not None:
                try:
                    distance = haversine(lat, lng, plat, plng)
                except Exception:
                    distance = None

            item = {
                'pharmacy_name': profile.pharmacy_name if profile else '',
                'pharmacist_username': pharmacist.username if pharmacist else '',
                'latitude': plat,
                'longitude': plng,
                'current_stock': inv.current_stock,
                'distance_km': round(distance, 3) if distance is not None else None,
            }

            # apply radius filter if requested
            if radius_km is not None and item['distance_km'] is not None:
                if item['distance_km'] <= radius_km:
                    results.append(item)
            else:
                results.append(item)

        # sort by distance when available else by current_stock desc
        if lat is not None and lng is not None:
            results.sort(key=lambda r: (r['distance_km'] is None, r['distance_km'] if r['distance_km'] is not None else 9999))
        else:
            results.sort(key=lambda r: -int(r.get('current_stock') or 0))

        return Response(results)
