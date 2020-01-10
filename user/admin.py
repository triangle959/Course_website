from django.contrib import admin

# Register your models here.


from .models import UserProfile,ClassInfo


#UserProfile模型的管理器
@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('id', 'username', 'nickname', 'add_time', 'update_time')

#ClassInfo模型的管理器
@admin.register(ClassInfo)
class ClassInfoAdmin(admin.ModelAdmin):
    list_display = ('class_name', 'count')