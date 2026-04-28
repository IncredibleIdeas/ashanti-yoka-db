"""Role-based access control"""
from config.settings import ROLES

def has_permission(user_role, required_role):
    """Check if user has required permission level"""
    role_hierarchy = {
        ROLES['SUPER_ADMIN']: 3,
        ROLES['ADMIN']: 2,
        ROLES['BRANCH_EXECUTIVE']: 1
    }
    
    user_level = role_hierarchy.get(user_role, 0)
    required_level = role_hierarchy.get(required_role, 0)
    
    return user_level >= required_level

def get_user_permissions(user_role):
    """Get all permissions for a user role"""
    base_permissions = {
        'view_members': True,
        'register_members': True,
        'edit_own_members': user_role in [ROLES['SUPER_ADMIN'], ROLES['ADMIN'], ROLES['BRANCH_EXECUTIVE']],
        'delete_members': user_role in [ROLES['SUPER_ADMIN'], ROLES['ADMIN']],
        'view_analytics': True,
        'export_data': True,
    }
    
    admin_permissions = {
        'import_data': user_role in [ROLES['SUPER_ADMIN'], ROLES['ADMIN']],
        'manage_branches': user_role in [ROLES['SUPER_ADMIN'], ROLES['ADMIN']],
        'manage_users': user_role == ROLES['SUPER_ADMIN'],
        'view_audit_log': user_role == ROLES['SUPER_ADMIN'],
        'configure_email': user_role == ROLES['SUPER_ADMIN'],
        'customize_theme': user_role == ROLES['SUPER_ADMIN'],
    }
    
    return {**base_permissions, **admin_permissions}