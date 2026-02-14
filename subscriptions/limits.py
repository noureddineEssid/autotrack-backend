from datetime import datetime
from django.db.models import Sum
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from vehicles.models import Vehicle
from documents.models import Document
from maintenances.models import Maintenance
from diagnostics.models import Diagnostic
from .plan_catalog import get_plan


def _month_range(now: datetime | None = None):
    now = now or timezone.now()
    start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    if start.month == 12:
        end = start.replace(year=start.year + 1, month=1)
    else:
        end = start.replace(month=start.month + 1)
    return start, end


def get_usage_counts(user):
    start, end = _month_range()

    vehicles_count = Vehicle.objects.filter(owner=user).count()
    documents_qs = Document.objects.filter(user=user)
    documents_count = documents_qs.count()
    storage_bytes = documents_qs.aggregate(total=Sum('file_size')).get('total') or 0

    maintenances_count = Maintenance.objects.filter(
        vehicle__owner=user,
        service_date__gte=start,
        service_date__lt=end,
    ).count()

    diagnostics_count = Diagnostic.objects.filter(
        user=user,
        created_at__gte=start,
        created_at__lt=end,
    ).count()

    return {
        'vehicles': vehicles_count,
        'documents': documents_count,
        'storage_bytes': storage_bytes,
        'maintenances': maintenances_count,
        'diagnostics': diagnostics_count,
    }


def get_plan_limits(plan_code: str):
    plan = get_plan(plan_code) or get_plan('free')
    return plan['limits']


def check_limit(user, resource: str, amount: int = 1, extra_bytes: int = 0):
    usage = get_usage_counts(user)
    limits = get_plan_limits(getattr(user, 'active_plan_code', None) or get_user_plan_code(user))

    if resource == 'storage':
        limit_mb = limits.get('storage_mb', -1)
        if limit_mb == -1:
            return True, {'current': usage['storage_bytes'], 'limit': -1}
        new_total = usage['storage_bytes'] + extra_bytes
        limit_bytes = limit_mb * 1024 * 1024
        return new_total <= limit_bytes, {
            'current': usage['storage_bytes'],
            'limit': limit_bytes,
            'limit_mb': limit_mb,
            'new_total': new_total,
        }

    limit = limits.get(resource, -1)
    if limit == -1:
        return True, {'current': usage.get(resource, 0), 'limit': -1}

    current = usage.get(resource, 0)
    return current + amount <= limit, {
        'current': current,
        'limit': limit,
        'requested': amount,
    }


def get_user_plan_code(user):
    try:
        from .models import Subscription
        subscription = Subscription.objects.filter(user=user, status='active').order_by('-created_at').first()
        if subscription:
            return subscription.plan_code
    except Exception:
        pass
    return 'free'


def enforce_limit(user, resource: str, amount: int = 1, extra_bytes: int = 0):
    allowed, meta = check_limit(user, resource, amount=amount, extra_bytes=extra_bytes)
    if allowed:
        return

    if resource == 'storage':
        limit_mb = meta.get('limit_mb')
        raise ValidationError({
            'detail': f"Limite de stockage atteinte ({limit_mb} Mo).",
            'resource': resource,
            'current_bytes': meta.get('current'),
            'limit_mb': limit_mb,
        })

    raise ValidationError({
        'detail': f"Limite atteinte pour {resource}.",
        'resource': resource,
        'current': meta.get('current'),
        'limit': meta.get('limit'),
    })
