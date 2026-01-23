"""
Views for booking system
"""

from datetime import datetime, timedelta
from django.db.models import Count, Avg, Q, Sum
from django.utils import timezone
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import GarageService, GarageAvailability, Booking, BookingReview
from .serializers import (
    GarageServiceSerializer,
    GarageAvailabilitySerializer,
    BookingSerializer,
    CreateBookingSerializer,
    BookingReviewSerializer,
    BookingStatsSerializer,
    AvailableSlotSerializer
)


class GarageServiceViewSet(viewsets.ModelViewSet):
    """ViewSet for garage services"""
    
    serializer_class = GarageServiceSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Get services, optionally filtered by garage"""
        queryset = GarageService.objects.filter(is_active=True)
        
        # Filter by garage
        garage_id = self.request.query_params.get('garage')
        if garage_id:
            queryset = queryset.filter(garage_id=garage_id)
        
        # Filter by category
        category = self.request.query_params.get('category')
        if category:
            queryset = queryset.filter(category=category)
        
        return queryset.select_related('garage')


class GarageAvailabilityViewSet(viewsets.ModelViewSet):
    """ViewSet for garage availability"""
    
    serializer_class = GarageAvailabilitySerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Get availability, filtered by garage"""
        queryset = GarageAvailability.objects.filter(is_active=True)
        
        # Filter by garage
        garage_id = self.request.query_params.get('garage')
        if garage_id:
            queryset = queryset.filter(garage_id=garage_id)
        
        return queryset.select_related('garage')


class BookingViewSet(viewsets.ModelViewSet):
    """ViewSet for bookings"""
    
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        """Use different serializer for creation"""
        if self.action == 'create':
            return CreateBookingSerializer
        return BookingSerializer
    
    def get_queryset(self):
        """Get user's bookings with filters"""
        queryset = Booking.objects.filter(user=self.request.user)
        
        # Filter by status
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # Filter by garage
        garage_id = self.request.query_params.get('garage')
        if garage_id:
            queryset = queryset.filter(garage_id=garage_id)
        
        # Filter by vehicle
        vehicle_id = self.request.query_params.get('vehicle')
        if vehicle_id:
            queryset = queryset.filter(vehicle_id=vehicle_id)
        
        # Filter upcoming
        upcoming = self.request.query_params.get('upcoming')
        if upcoming == 'true':
            queryset = queryset.filter(
                booking_date__gte=timezone.now().date(),
                status__in=['pending', 'confirmed']
            )
        
        # Filter past
        past = self.request.query_params.get('past')
        if past == 'true':
            queryset = queryset.filter(
                Q(booking_date__lt=timezone.now().date()) |
                Q(status__in=['completed', 'cancelled', 'no_show'])
            )
        
        return queryset.select_related('garage', 'vehicle', 'service', 'cancelled_by')
    
    def perform_create(self, serializer):
        """Create booking and send confirmation email"""
        booking = serializer.save()
        
        # Send confirmation email (implement in tasks.py)
        from .tasks import send_booking_confirmation_email
        send_booking_confirmation_email.delay(str(booking.id))
    
    @action(detail=True, methods=['post'])
    def confirm(self, request, pk=None):
        """Confirm a booking"""
        booking = self.get_object()
        
        if booking.status != 'pending':
            return Response(
                {'error': 'Seules les réservations en attente peuvent être confirmées'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        booking.confirm()
        
        # Send confirmation email
        from .tasks import send_booking_confirmed_email
        send_booking_confirmed_email.delay(str(booking.id))
        
        serializer = self.get_serializer(booking)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def start(self, request, pk=None):
        """Start service for booking"""
        booking = self.get_object()
        
        if booking.status != 'confirmed':
            return Response(
                {'error': 'Seules les réservations confirmées peuvent être démarrées'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        booking.start_service()
        serializer = self.get_serializer(booking)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        """Complete a booking"""
        booking = self.get_object()
        
        if booking.status != 'in_progress':
            return Response(
                {'error': 'Seules les réservations en cours peuvent être terminées'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        final_price = request.data.get('final_price')
        booking.complete(final_price=final_price)
        
        # Send completion email with review request
        from .tasks import send_booking_completed_email
        send_booking_completed_email.delay(str(booking.id))
        
        serializer = self.get_serializer(booking)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Cancel a booking"""
        booking = self.get_object()
        
        if not booking.can_cancel:
            return Response(
                {'error': 'Cette réservation ne peut plus être annulée (moins de 24h avant le rendez-vous)'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        reason = request.data.get('reason', '')
        booking.cancel(reason=reason, cancelled_by=request.user)
        
        # Send cancellation email
        from .tasks import send_booking_cancelled_email
        send_booking_cancelled_email.delay(str(booking.id))
        
        serializer = self.get_serializer(booking)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def no_show(self, request, pk=None):
        """Mark customer as no-show"""
        booking = self.get_object()
        
        if not booking.is_today:
            return Response(
                {'error': 'Vous ne pouvez marquer comme absent qu\'une réservation du jour'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        booking.mark_no_show()
        serializer = self.get_serializer(booking)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def upcoming(self, request):
        """Get upcoming bookings (next 7 days)"""
        bookings = self.get_queryset().filter(
            booking_date__gte=timezone.now().date(),
            booking_date__lte=timezone.now().date() + timedelta(days=7),
            status__in=['pending', 'confirmed']
        ).order_by('booking_date', 'booking_time')
        
        serializer = self.get_serializer(bookings, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def today(self, request):
        """Get today's bookings"""
        bookings = self.get_queryset().filter(
            booking_date=timezone.now().date(),
            status__in=['pending', 'confirmed', 'in_progress']
        ).order_by('booking_time')
        
        serializer = self.get_serializer(bookings, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Get booking statistics"""
        queryset = self.get_queryset()
        
        # Count by status
        total_bookings = queryset.count()
        pending = queryset.filter(status='pending').count()
        confirmed = queryset.filter(status='confirmed').count()
        in_progress = queryset.filter(status='in_progress').count()
        completed = queryset.filter(status='completed').count()
        cancelled = queryset.filter(status='cancelled').count()
        no_show = queryset.filter(status='no_show').count()
        
        # Upcoming bookings
        upcoming_7_days = queryset.filter(
            booking_date__gte=timezone.now().date(),
            booking_date__lte=timezone.now().date() + timedelta(days=7),
            status__in=['pending', 'confirmed']
        ).count()
        
        today = queryset.filter(
            booking_date=timezone.now().date(),
            status__in=['pending', 'confirmed', 'in_progress']
        ).count()
        
        # Revenue
        total_revenue = queryset.filter(
            status='completed',
            final_price__isnull=False
        ).aggregate(total=Sum('final_price'))['total'] or 0
        
        # Average rating
        average_rating = BookingReview.objects.filter(
            booking__user=request.user
        ).aggregate(avg=Avg('rating'))['avg'] or 0
        
        # By service
        by_service = dict(
            queryset.filter(service__isnull=False)
            .values('service__name')
            .annotate(count=Count('id'))
            .values_list('service__name', 'count')
        )
        
        # By garage
        by_garage = dict(
            queryset.values('garage__name')
            .annotate(count=Count('id'))
            .values_list('garage__name', 'count')
        )
        
        stats_data = {
            'total_bookings': total_bookings,
            'pending': pending,
            'confirmed': confirmed,
            'in_progress': in_progress,
            'completed': completed,
            'cancelled': cancelled,
            'no_show': no_show,
            'upcoming_7_days': upcoming_7_days,
            'today': today,
            'total_revenue': total_revenue,
            'average_rating': round(average_rating, 2),
            'by_service': by_service,
            'by_garage': by_garage,
        }
        
        serializer = BookingStatsSerializer(stats_data)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def available_slots(self, request):
        """Get available time slots for a garage and date"""
        garage_id = request.query_params.get('garage')
        date_str = request.query_params.get('date')
        
        if not garage_id or not date_str:
            return Response(
                {'error': 'Paramètres garage et date requis'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            booking_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            return Response(
                {'error': 'Format de date invalide (YYYY-MM-DD attendu)'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        weekday = booking_date.weekday()
        
        # Get garage availability for this weekday
        availabilities = GarageAvailability.objects.filter(
            garage_id=garage_id,
            weekday=weekday,
            is_active=True
        )
        
        available_slots = []
        
        for availability in availabilities:
            # Generate time slots (every 30 minutes)
            current_time = datetime.combine(booking_date, availability.start_time)
            end_time = datetime.combine(booking_date, availability.end_time)
            
            while current_time < end_time:
                slot_time = current_time.time()
                
                # Count existing bookings for this slot
                existing_bookings = Booking.objects.filter(
                    garage_id=garage_id,
                    booking_date=booking_date,
                    booking_time=slot_time,
                    status__in=['pending', 'confirmed', 'in_progress']
                ).count()
                
                available_spots = availability.max_bookings_per_slot - existing_bookings
                
                if available_spots > 0:
                    available_slots.append({
                        'date': booking_date,
                        'time': slot_time,
                        'available_spots': available_spots,
                        'garage_id': garage_id
                    })
                
                current_time += timedelta(minutes=30)
        
        serializer = AvailableSlotSerializer(available_slots, many=True)
        return Response(serializer.data)


class BookingReviewViewSet(viewsets.ModelViewSet):
    """ViewSet for booking reviews"""
    
    serializer_class = BookingReviewSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Get reviews for user's bookings"""
        return BookingReview.objects.filter(
            booking__user=self.request.user
        ).select_related('booking', 'booking__garage', 'booking__service')
    
    @action(detail=False, methods=['get'])
    def for_garage(self, request):
        """Get all reviews for a specific garage"""
        garage_id = request.query_params.get('garage')
        if not garage_id:
            return Response(
                {'error': 'Paramètre garage requis'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        reviews = BookingReview.objects.filter(
            booking__garage_id=garage_id
        ).select_related('booking', 'booking__garage', 'booking__service')
        
        serializer = self.get_serializer(reviews, many=True)
        return Response(serializer.data)
