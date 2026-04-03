
def can_hijack(hijacker, hijacked):
    """
    Política de seguridad para impersonación:
    1. El hijacker debe ser superusuario o staff.
    2. El hijacked NO puede ser superusuario (protección de cuenta raíz).
    3. Un staff no puede impersonar a otro staff (opcional, pero más seguro).
    """
    if not hijacker.is_staff and not hijacker.is_superuser:
        return False
    
    if hijacked.is_superuser:
        return False
        
    if hijacker.is_staff and not hijacker.is_superuser:
        if hijacked.is_staff:
            return False
            
    return True
