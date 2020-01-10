from django.contrib.auth import get_user_model
from django.db import models

# Create your models here.
from datetime import datetime

from django.utils import timezone

from user.models import UserProfile, ClassInfo

User = get_user_model()

class ExamList(models.Model):
    name = models.CharField(max_length=100, verbose_name=u"试卷名", default="")
    decs = models.CharField(max_length=500, verbose_name=u"试卷说明", default="")
    add_time = models.DateField(default=datetime.now, verbose_name=u"添加时间")

    class Meta:
        verbose_name = "试卷类型"
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.name


class Question(models.Model):
    course = models.ForeignKey(ExamList.__name__, verbose_name=u"课程", on_delete=models.CASCADE)
    questionType = models.CharField(max_length=2, choices=(("xz", u"选择题"), ("pd", u"判断题"), ("wd", u"问答")), default="xz", verbose_name=u"题目类型")
    content = models.TextField(verbose_name=u"题目内容")
    answer = models.TextField(verbose_name=u"正确答案")
    choice_a = models.TextField(verbose_name=u"A选项", default="A.")
    choice_b = models.TextField(verbose_name=u"B选项", default="B.")
    choice_c = models.TextField(verbose_name=u"C选项", default="C.")
    choice_d = models.TextField(verbose_name=u"D选项", default="D.")
    score = models.IntegerField(verbose_name=u"分值", default=0)
    note = models.TextField(verbose_name=u"备注信息", default= u"问答题在此处做答")
    boolt = models.TextField(verbose_name=u"判断正误正确选项", default= "True")
    boolf = models.TextField(verbose_name=u"判断正误错误选项", default= "False")
    add_time = models.DateField(default=datetime.now, verbose_name=u"添加时间")

    class Meta:
        verbose_name = u"题库"
        verbose_name_plural = verbose_name

    def get_content_display(self, field):
        return self.content

    def __unicode__(self):
        model = Question
        return "{0}(题干:{1} | 正确答案:{2} )".format(self.course.name, self.content, self.answer)



class Shixun_Info(models.Model):
    """
        学生选题表
    """
    CHOICES = (
        (-1, "None"),
        (0, "False"),
        (1, "True"),
    )
    stu_id = models.CharField(max_length=20, default="", verbose_name="学号")
    stu_name = models.CharField(max_length=20, default="", verbose_name="姓名")
    class_name = models.CharField(max_length=20, default="", verbose_name="班级名")
    subject = models.TextField(verbose_name="实训选题", null=True, blank=True)
    is_start = models.IntegerField(choices=CHOICES, default=CHOICES[0][0], verbose_name="是否开放实训选题")
    end_time = models.DateField(verbose_name="选题截至时间", default=timezone.now)
    is_pass = models.IntegerField(choices=CHOICES, default=CHOICES[0][0], verbose_name="是否通过选题")
    suggestion = models.TextField(verbose_name="选题建议", null=True, blank=True)
    score = models.IntegerField(verbose_name="实训成绩", default=0)

    class Meta:
        verbose_name = "实训选题"
        verbose_name_plural = verbose_name