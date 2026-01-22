"""
Permissions personnalisées pour le contrôle d'accès basé sur les plans d'abonnement
Équivalent du PlanAccessGuard NestJS
"""
from rest_framework.permissions import BasePermission
from subscriptions.models import Subscription
from plans.models import Plan


class HasActivePlan(BasePermission):
    """
    Permission pour vérifier qu'un utilisateur a un abonnement actif
    """
    
    message = "Aucun abonnement actif. Veuillez souscrire à un plan pour continuer."
    
    def has_permission(self, request, view):
        """Vérifier que l'utilisateur a un abonnement actif"""
        if not request.user or not request.user.is_authenticated:
            return False
        
        try:
            subscription = Subscription.objects.select_related('plan').get(
                user=request.user,
                status='active'
            )
            return subscription is not None
        except Subscription.DoesNotExist:
            return False


class IsFreePlan(BasePermission):
    """
    Permission pour fonctionnalités FREE (disponibles pour tous les plans)
    """
    
    message = "Cette fonctionnalité nécessite un compte gratuit."
    
    def has_permission(self, request, view):
        """Tous les utilisateurs authentifiés ont accès FREE"""
        return request.user and request.user.is_authenticated


class IsStandardPlan(BasePermission):
    """
    Permission pour fonctionnalités STANDARD minimum
    """
    
    message = "📦 Cette fonctionnalité nécessite au minimum le plan Standard (9.99€/mois). Mettez à niveau votre abonnement pour y accéder."
    
    ALLOWED_PLAN_TYPES = ['standard', 'premium']
    
    def has_permission(self, request, view):
        """Vérifier que l'utilisateur a un plan Standard ou supérieur"""
        if not request.user or not request.user.is_authenticated:
            return False
        
        try:
            subscription = Subscription.objects.select_related('plan').get(
                user=request.user,
                status='active'
            )
            
            if not subscription.plan:
                return False
            
            return subscription.plan.type in self.ALLOWED_PLAN_TYPES
            
        except Subscription.DoesNotExist:
            return False


class IsPremiumPlan(BasePermission):
    """
    Permission pour fonctionnalités PREMIUM uniquement
    """
    
    message = "⭐ Cette fonctionnalité nécessite le plan Premium (19.99€/mois). Mettez à niveau votre abonnement pour y accéder."
    
    def has_permission(self, request, view):
        """Vérifier que l'utilisateur a un plan Premium"""
        if not request.user or not request.user.is_authenticated:
            return False
        
        try:
            subscription = Subscription.objects.select_related('plan').get(
                user=request.user,
                status='active'
            )
            
            if not subscription.plan:
                return False
            
            return subscription.plan.type == 'premium'
            
        except Subscription.DoesNotExist:
            return False


class RequiresPlanLevel(BasePermission):
    """
    Permission générique configurable par niveau de plan
    Usage: Hériter et définir required_plan_level
    
    Example:
        class MyView(APIView):
            permission_classes = [RequiresPlanLevel]
            required_plan_level = 'standard'  # ou 'premium'
    """
    
    PLAN_HIERARCHY = {
        'free': 0,
        'standard': 1,
        'premium': 2
    }
    
    def has_permission(self, request, view):
        """Vérifier le niveau de plan requis"""
        if not request.user or not request.user.is_authenticated:
            self.message = "Authentification requise"
            return False
        
        # Récupérer le niveau requis depuis la vue
        required_level = getattr(view, 'required_plan_level', 'free')
        
        # Si FREE, tous les utilisateurs authentifiés passent
        if required_level == 'free':
            return True
        
        try:
            subscription = Subscription.objects.select_related('plan').get(
                user=request.user,
                status='active'
            )
            
            if not subscription.plan:
                self.message = "Plan d'abonnement introuvable. Veuillez contacter le support."
                return False
            
            # Comparer les niveaux
            user_level = self.PLAN_HIERARCHY.get(subscription.plan.type, 0)
            required = self.PLAN_HIERARCHY.get(required_level, 0)
            
            if user_level >= required:
                return True
            
            # Message personnalisé selon le niveau requis
            if required_level == 'standard':
                self.message = "📦 Cette fonctionnalité nécessite au minimum le plan Standard (9.99€/mois)."
            elif required_level == 'premium':
                self.message = "⭐ Cette fonctionnalité nécessite le plan Premium (19.99€/mois)."
            
            return False
            
        except Subscription.DoesNotExist:
            self.message = "Aucun abonnement trouvé. Veuillez souscrire à un plan pour continuer."
            return False
