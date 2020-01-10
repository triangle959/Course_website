from django.shortcuts import render

# Create your views here.

from io import BytesIO
from datetime import datetime
from django.shortcuts import render, HttpResponse, redirect
from django.urls import reverse
from django.core.cache import cache
from django.views.generic import View
from django.http import Http404
from django.db.models import Q
from utils.check_code import create_validate_code
from .models import UserProfile, UserFollowing, ClassInfo
from operation.models import TopicVote, FavoriteNode, Topic, UserDetails, SignedInfo
from exam.models import Shixun_Info
from topic.models import TopicCategory
from .forms import SignupForm, SigninForm



# Create your views here.


def check_code(request):
    """
    验证码
    :param request:
    :return:
    """
    stream = BytesIO()
    img, code = create_validate_code()
    img.save(stream, 'PNG')
    request.session["CheckCode"] = code     #session配置
    return HttpResponse(stream.getvalue())


class SignupView(View):
    def get(self, request):
        # class_info = ClassInfo.objects.all().values()
        # class_info_list = list(class_info)    {'class_list': class_info_list}
        obj = SignupForm()
        return render(request, 'user/signup.html', locals())

    def post(self, request):
        has_error = True
        if request.POST.get('check_code', None):
            # 判断验证码
            if request.session['CheckCode'].upper() == request.POST.get('check_code').upper():
                # Form验证
                obj = SignupForm(request.POST)
                if obj.is_valid():
                    has_error = False
                    username = obj.cleaned_data['username']
                    password = obj.cleaned_data['password']
                    class_name = obj.cleaned_data['classInfo']
                    nickname = obj.cleaned_data['nickname']
                    email = obj.cleaned_data['email']
                    mobile = obj.cleaned_data['mobile']
                    #class_obj = ClassInfo()
                    # 保存用户
                    user_obj = UserProfile()
                    user_obj.username = username
                    user_obj.nickname = nickname
                    user_obj.email = email
                    user_obj.class_name = class_name
                    user_obj.mobile = mobile
                    user_obj.set_password(password)
                    user_obj.save()
                    # 注册成功，创建用户details 表
                    UserDetails.objects.create(user_id=user_obj.id)
                    Shixun_Info.objects.create(stu_id=user_obj.username,
                                               stu_name=user_obj.nickname,
                                               class_name=user_obj.class_name)
                    # 注册成功后默认收藏tab节点
                    # favorite_node_obj = FavoriteNode()
                    # favorite_node_obj.user_id = user_obj.id
                    # favorite_node_obj.favorite = 1
                    # favorite_node_obj.node = TopicCategory.objects.filter(category_type=1)
                    # favorite_node_obj.save()
                    # for item in favorite_node_obj:
                    #     item.save()
                    #     request.session['user_info']['favorite_node_num'] += 1
                    # 跳转到登录页
                    return redirect(reverse('signin'))
                else:
                    print(obj.errors)
                    return render(request, 'user/signup.html', locals())
            else:
                code_error = "验证码错误"
                obj = SignupForm()
        else:
            code_error = "请输入验证码"
            obj = SignupForm()
        return render(request, 'user/signup.html', locals())


class SigninView(View):
    def get(self, request):
        next_url = request.GET.get('next', None)
        return render(request, 'user/signin.html', locals())

    def post(self, request):
        has_error = True
        if request.POST.get('check_code', None):
            if request.session['CheckCode'].upper() == request.POST.get('check_code').upper():
                obj = SigninForm(request.POST)
                if obj.is_valid():
                    username = obj.cleaned_data['username']
                    password = obj.cleaned_data['password']
                    user_obj = UserProfile.objects.filter(Q(username=username) | Q(email=username)).first()
                    if user_obj:
                        if user_obj.check_password(password):
                            # 账号密码正确，登录成功 修改最后登录时间
                            user_obj.last_login = datetime.now()
                            # 获取用户本次session_key 记录到数据库中，以便在其他地方修改此用户的session 信息
                            user_obj.session = request.session.session_key
                            user_obj.save()

                            # 用户详细信息表 注册时已经创建，这里是防止admin等用户未创建产生的BUG
                            user_detail = UserDetails.objects.filter(user_id=user_obj.id).first()
                            if not user_detail:
                                user_detail = UserDetails.objects.create(user_id=user_obj.id)

                            # 获取用户基础信息，存放到session中，方便频繁调用
                            # 获取签到状态
                            signed_obj = SignedInfo.objects.filter(user_id=user_obj.id,
                                                                   date=datetime.now().strftime('%Y%m%d'),
                                                                   status=True).first()
                            if signed_obj:
                                signed_status = True
                            else:
                                signed_status = False
                            # 该用户的班级是否开放实训选题，存入session
                            class_obj = ClassInfo.objects.get(class_name=user_obj.class_name)
                            class_id = class_obj.__dict__['id']

                            # 实训选题表 注册时已经创建，这里是防止admin等用户未创建产生的BUG
                            Shixun_obj = Shixun_Info.objects.filter(stu_id=user_obj.username).first()
                            # if not Shixun_obj:
                            #     Shixun_obj = Shixun_Info.objects.create(stu_id=user_obj.username,
                            #                                stu_name=user_obj.nickname,
                            #                                class_name=user_obj.class_name)

                            # 组装用户信息，并写入session中
                            if user_obj.is_superuser:
                                user_info = {
                                    'username': username,
                                    'uid': user_obj.id,
                                    'avatar': user_obj.avatar,
                                    'mobile': user_obj.mobile,
                                    'favorite_node_num': FavoriteNode.objects.filter(favorite=1, user=user_obj).count(),
                                    'favorite_topic_num': TopicVote.objects.filter(favorite=1, user=user_obj).count(),
                                    'following_user_num': UserFollowing.objects.filter(is_following=1,
                                                                                       user=user_obj).count(),
                                    'class_name': user_obj.class_name,
                                    'nick_name': user_obj.nickname,
                                    'show_balance': user_detail.show_balance,
                                    'balance': user_detail.balance,
                                    'daily_mission': signed_status,
                                    'is_superuser': user_obj.is_superuser,
                                }
                            else:
                                user_info = {
                                    'username': username,
                                    'uid': user_obj.id,
                                    'avatar': user_obj.avatar,
                                    'mobile': user_obj.mobile,
                                    'favorite_node_num': FavoriteNode.objects.filter(favorite=1, user=user_obj).count(),
                                    'favorite_topic_num': TopicVote.objects.filter(favorite=1, user=user_obj).count(),
                                    'following_user_num': UserFollowing.objects.filter(is_following=1,
                                                                                       user=user_obj).count(),
                                    'class_name': user_obj.class_name,
                                    'nick_name': user_obj.nickname,
                                    'show_balance': user_detail.show_balance,
                                    'balance': user_detail.balance,
                                    'daily_mission': signed_status,
                                    'xuanti_start': Shixun_obj.is_start,
                                    'is_superuser': user_obj.is_superuser,
                                }
                            # 登陆后页面跳转
                            if request.POST.get('next', None):
                                next_url = request.POST.get('next')
                            else:
                                next_url = reverse('new_index')
                            # 如果用户定义了登录后跳转，则跳转到用户指定页面
                            if user_detail.my_home:
                                next_url = user_detail.my_home
                            resp = redirect(next_url)
                            request.session['user_info'] = user_info
                            online_key = 'count_online_id_{_id}_session_{_session}'.format(
                                _id=request.session.get('user_info')['uid'], _session=request.session.session_key)
                            cache.set(online_key, 'true')
                            return resp
                        else:
                            user_error = '用户或密码错误'
                    else:
                        user_error = '用户不存在'
            else:
                code_error = "验证码错误"
        else:
            code_error = "请输入验证码"
        return render(request, 'user/signin.html', locals())


class SignoutView(View):
    def get(self, request):
        # 如果用户登录了
        if request.session.get('user_info', None):
            # 删除登录用户统计信息
            online_key = 'count_online_id_{_id}_session_{_session}'.format(
                _id=request.session.get('user_info')['uid'], _session=request.session.session_key)
            cache.delete(online_key)
            # 清除 session 信息
            request.session.flush()
        return render(request, 'user/signout.html')


class MemberView(View):
    def get(self, request, username):
        try:
            # 获取链接指向的用户名的obj
            user_obj = UserProfile.objects.get(username=username)
            # 通过当前查看的用户名获取用户id和session信息，然后在cache中查找此key
            # 1 判断用户是否在线 有此key  在线， 没有此key 离线 这里用此方式
            # 2 通过session 根据有没有此用户在数据库中存储的session 判断
            online_key = 'count_online_id_{_id}_session_{_session}'.format(
                _id=user_obj.id, _session=user_obj.session)
            online_status = cache.get(online_key)
            # 获取作者是连接中的用户的Topic主题
            topic_obj = Topic.objects.filter(author=user_obj).select_related('category').order_by('-add_time')
            if request.session.get('user_info', None):
                # 获取当前用户是否following 此用户 根据此来调整页面显示信息
                is_following = UserFollowing.objects.values_list('is_following').filter(is_following=1,
                                                                                        user_id=request.session.get(
                                                                                            'user_info')['uid'],
                                                                                        following=user_obj).first()
                # 获取当前用户是否block 此用户
                is_block = UserFollowing.objects.values_list('is_block').filter(is_block=1, user_id=request.session.get(
                    'user_info')['uid'], following=user_obj).first()

            return render(request, 'user/member.html', locals())
        # 没有此用户，指向没有的连接，返回404
        except UserProfile.DoesNotExist:
            raise Http404("Not Find This User")


