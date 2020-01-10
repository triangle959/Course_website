from django.contrib import admin

# Register your models here.

from .models import Topic
from .models import TopicCategory

#Topic模型管理器
@admin.register(Topic)
class TopicAdmin(admin.ModelAdmin):
    list_display = ("category", "author", "topic_sn", "title", "add_time")

#TopicCategory模型管理器
@admin.register(TopicCategory)
class TopicCategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "category_type", "add_time", "update_time")

