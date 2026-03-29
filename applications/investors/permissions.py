def can_access_investor(user, investor):
    return user.is_staff or user.is_superuser or investor.user_id == user.id
