from django.contrib import admin

# Register your models here.
from .models import UserScore

@admin.register(UserScore)
class UserScoreAdmin(admin.ModelAdmin):

    list_display = ("user", "exam", "total", "add_time",)

    # 筛选器
    list_filter = ('exam',)  # 过滤器
    search_fields = ('user', 'exam',)  # 搜索字段
    date_hierarchy = 'add_time'  # 详细时间分层筛选　