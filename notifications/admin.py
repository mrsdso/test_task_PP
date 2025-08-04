from django.contrib import admin
from .models import UserGroup, NotificationUser, NotificationMessage, NotificationLog


@admin.register(UserGroup)
class UserGroupAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'user_count', 'created_at')
    search_fields = ('name', 'description')
    list_filter = ('created_at',)
    
    def user_count(self, obj):
        return obj.users.filter(is_active=True).count()
    user_count.short_description = 'Активных пользователей'


@admin.register(NotificationUser)
class NotificationUserAdmin(admin.ModelAdmin):
    list_display = ('external_id', 'email', 'phone', 'telegram', 'group', 'is_active', 'created_at')
    list_filter = ('group', 'is_active', 'created_at')
    search_fields = ('email', 'phone', 'telegram', 'external_id')
    list_editable = ('is_active',)
    list_per_page = 50
    
    fieldsets = (
        (None, {
            'fields': ('external_id', 'email', 'phone', 'telegram')
        }),
        ('Группа и статус', {
            'fields': ('group', 'is_active')
        }),
        ('Даты', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ('created_at', 'updated_at')


@admin.register(NotificationMessage)
class NotificationMessageAdmin(admin.ModelAdmin):
    list_display = ('title', 'created_by', 'is_sent', 'sent_at', 'created_at')
    list_filter = ('is_sent', 'created_at', 'sent_at', 'created_by')
    search_fields = ('title', 'content')
    filter_horizontal = ('target_groups',)
    readonly_fields = ('created_at', 'sent_at', 'is_sent')
    
    fieldsets = (
        (None, {
            'fields': ('title', 'content')
        }),
        ('Настройки доставки', {
            'fields': ('delivery_methods', 'target_groups', 'send_to_all')
        }),
        ('Статус', {
            'fields': ('is_sent', 'sent_at', 'created_by', 'created_at'),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not change:  # Только при создании
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(NotificationLog)
class NotificationLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'message_title', 'delivery_method', 'status', 'sent_at')
    list_filter = ('delivery_method', 'status', 'sent_at')
    search_fields = ('user__email', 'user__phone', 'user__telegram', 'message__title')
    readonly_fields = ('message', 'user', 'delivery_method', 'status', 'error_message', 'sent_at')
    list_per_page = 100
    
    def message_title(self, obj):
        return obj.message.title
    message_title.short_description = 'Сообщение'
    
    def has_add_permission(self, request):
        return False  # Запрещаем создание логов через админку
    
    def has_change_permission(self, request, obj=None):
        return False  # Запрещаем изменение логов через админку


# Настройка админ панели
admin.site.site_header = "Система уведомлений"
admin.site.site_title = "Система уведомлений"
admin.site.index_title = "Панель управления"
