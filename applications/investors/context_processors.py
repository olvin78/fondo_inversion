from .models import Communication, Investor

def communication_notifications(request):
    if not request.user.is_authenticated:
        return {}
    
    try:
        # Intentamos obtener el perfil de inversor asociado al usuario
        investor = Investor.objects.get(user=request.user)
        # Contamos las comunicaciones no leídas específicamente para este inversor
        unread_count = Communication.objects.filter(investor=investor, is_read=False).count()
        return {
            'unread_communications_count': unread_count
        }
    except Investor.DoesNotExist:
        # Si el usuario no tiene un perfil de inversor (ej. es un admin puro)
        return {}
