from itertools import chain

from django.shortcuts import render

# Create your views here.
from django.views import View
from exam.models import ExamList, Question, Shixun_Info
from operation.models import UserScore
import datetime as dt
from user.models import ClassInfo, UserProfile

class ExamListView(View):
    """试卷列表页面"""

    def get(self, request):
        exams = ExamList.objects.all()
        for i in exams:
            print(i.name, '**', i.id)
        return render(request, "exam/exam_list.html", {"exams": exams})

class ExamView(View):
    """试题列表页面"""
    def get(self, request, exam_id):
        if request.session.get('user_info'):
            exam_list = ExamList.objects.filter(id=exam_id)
            questions = Question.objects.filter(course_id=exam_id)
            question_list = []
            question_id_list = []
            for question in questions:
                question_list.append(question)
                question_id_list.append(question.id)

            title = exam_list[0]
            question_now = tuple(question_list)
            question_count = len(question_now)

            score_obj = UserScore.objects.filter(user_id=request.session.get('user_info')['uid'], exam_id=exam_id).first()
            print(exam_id)
            if score_obj:
                score = score_obj.total
                return render(request, "exam/has_exam.html", {"score": score, "title": title})
            return render(request, "exam/exam_question.html", {"question": question_now, "exam_id": exam_id,
                                                     "question_count": question_count, "title": title})
        else:
            return render(request, "user/signin.html")

    def post(self, request, exam_id):
        if request.session.get('user_info'):
            exam_list = ExamList.objects.filter(id=exam_id)
            questions = Question.objects.filter(course_id=exam_id)  # 找到所有试题
            question_id_list = []
            user_ans_dict = {}
            for question in questions:
                question_id_list.append(question.id)
            # 找到该用户所有的做题记录
            all_score = UserScore.objects.filter(user_id=request.session.get('user_info')['uid'])

            title = question.course.name
            # 分数记录
            user_score = UserScore()
            # 记录用户
            user_score.user_id = request.session.get('user_info')['uid']
            # 记录试卷名
            user_score.exam = ExamList.objects.get(pk=exam_id)
            # 记录做题时间
            user_score.add_time = dt.datetime.now()
            # 显示提交的题目编号列表
            print('post 方法里用户获取的题目编号为', question_id_list)
            temp_score = 0
            # 遍历每一道题
            for i in question_id_list:
                # 根据编号找到用户提交的对应题号的答案
                user_ans = request.POST.get(str(i), "")
                print(u'试题', i, u'收到的答案是', user_ans)

                # 获取题号为 i 的题目元组对象
                temp_question = Question.objects.get(pk=i)
                # 把正确答案与提交的答案比较
                if temp_question.answer == user_ans:
                    temp_score += temp_question.score
                    print("试题", temp_question.id, "答案正确")
                user_ans_dict[i] = [user_ans, temp_question.answer]
            state = 0

            #返回原题目用户答案题目答案
            question_list = []
            question_id_list = []
            for question in questions:
                question_list.append(question)
                question_id_list.append(question.id)
            question_all = tuple(question_list)
            question_count = len(question_all)

            print(user_ans_dict)
            print(type(user_ans_dict))
            user_score.total = temp_score
            score = user_score.total

            if state == 0:
                user_score.save()
            return render(request, "exam/score.html", locals())

class ShixunView(View):
    def get(self, request):
        if request.session.get('user_info'):
            is_over = True
            #学生选课信息
            Shixun_obj = Shixun_Info.objects.filter(stu_id=request.session.get('user_info')['username']).first()
            #利用chain合并多个queryset
            # Shixun_class_obj = chain(Shixun_Info.objects.filter(class_name=request.session.get('user_info')['class_name']),
            #                          UserProfile.objects.filter(id=request.session.get('user_info')['uid']))
            #班级选课信息
            Shixun_class_obj = Shixun_Info.objects.filter(class_name=request.session.get('user_info')['class_name'])
            if dt.date.today() <= Shixun_obj.end_time and Shixun_obj.is_start == 1:
                is_over = False
            else:
                is_over = True
            print(request.session.get('user_info')['is_superuser'])
            return render(request, "exam/xuanti.html", locals())
        return render(request, "exam/xuanti.html")

    def post(self,request):
        subject = request.POST.get('subject', None)
        Shixun_obj = Shixun_Info.objects.get(stu_id=request.session.get('user_info')['username'])
        Shixun_obj.subject = subject
        Shixun_obj.save()
        Shixun_class_obj = Shixun_Info.objects.filter(class_name=request.session.get('user_info')['class_name'])
        return render(request, "exam/xuanti.html", locals())