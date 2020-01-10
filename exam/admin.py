from django.contrib import admin
from django.utils.http import urlquote
# Register your models here.
from .models import ExamList
from .models import Question, Shixun_Info
import datetime
from django.http import HttpResponse
import xlwt
import os

#ExamList模型管理器
@admin.register(ExamList)
class ExamListAdmin(admin.ModelAdmin):
    list_display = ("name", "decs", "add_time")

#Question模型管理器
@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ("course", "questionType", "content", "add_time")

    # 筛选器
    list_filter = ('course', 'questionType')  # 过滤器
    search_fields = ('course', 'content')  # 搜索字段
    date_hierarchy = 'add_time'  # 详细时间分层筛选　

def start_xuanti(modeladmin, request, queryset):
    queryset.update(is_start=1, end_time=datetime.date.today() + datetime.timedelta(days=14))
start_xuanti.short_description = "批量开放选题"

def SaveExcel(self, request, queryset):
    list_queryset = list(queryset)
    filename = list_queryset[1].class_name + u"实训选题"
    filename = urlquote(filename)
    response = HttpResponse(content_type='application/ms-excel')
    response['Content-Disposition'] = 'attachment; filename=%s'%(filename) + '.xls'
    wb = xlwt.Workbook(encoding='utf-8')
    ws = wb.add_sheet('实训选题', cell_overwrite_ok=True)
    ws.col(3).width = 256*20
    # Sheet header, first row
    row_num = 0
    font_style = xlwt.XFStyle()
    font_style.font.bold = True
    columns = ['班级名', '学号', '姓名', '实训题目', '成绩']
    for col_num in range(len(columns)):
        ws.write(row_num, col_num, columns[col_num], font_style)
    # Sheet body, remaining rows
    font_style = xlwt.XFStyle()
    for row in queryset:
        row_num += 1
        ws.write(row_num, 0, row.class_name, font_style)
        ws.write(row_num, 1, row.stu_id, font_style)
        ws.write(row_num, 2, row.stu_name, font_style)
        ws.write(row_num, 3, row.subject, font_style)
        ws.write(row_num, 4, row.score, font_style)
    wb.save(response)
    return response
SaveExcel.short_description = "以表格形式下载"

@admin.register(Shixun_Info)
class ShixunAdmin(admin.ModelAdmin):
    list_display = ("stu_id", "stu_name", "class_name", "subject", "is_start", "end_time", "is_pass", "suggestion", "score")

    # 筛选器
    list_filter = ('class_name', 'subject')  # 过滤器
    ordering = ('subject',)
    search_fields = ('stu_id', 'subject')  # 搜索字段
    actions = [start_xuanti, SaveExcel]


