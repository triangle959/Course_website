from datetime import datetime
import markdown
import bleach
import os
from Course_website.settings import BASE_DIR
from extra.bleach_whitelist import markdown_tags, markdown_attrs
from django.shortcuts import render, redirect, HttpResponse
from django.urls import reverse
from django.db.models import F,Q
from django.views.generic import View
from django.contrib.auth import get_user_model
from django.utils.decorators import method_decorator
from utils.auth_decorator import login_auth
from django.http import Http404, FileResponse
from utils.some_utils import gender_topic_sn, save_upload_file
from utils.pagination import Paginator
from utils.update_balance import update_balance
from .models import TopicCategory, Topic, NodeLink, Comments
from operation.models import TopicVote, FavoriteNode
from user.models import UserFollowing,UserProfile
from .forms import NewTopicForm, MarkdownPreForm, CheckNodeForm, SuperNewTopicForm
from django.contrib.auth.models import Permission,Group,User

#User = get_user_model()
# Create your views here.

exts = ['markdown.extensions.extra', 'markdown.extensions.codehilite', 'markdown.extensions.tables',
        'markdown.extensions.toc']


class IndexView(View):
    def get(self, request):
        current_tab = request.GET.get('tab', 'tech')
        category_obj = TopicCategory.objects.filter(category_type=1)
        if current_tab == 'hot':
            category_obj.hot = True
            topic_obj = Topic.objects.select_related('author', 'category').all().order_by('-comment_num')[0:30]
            return render(request, 'topic/index.html', locals())
        category_children_obj = TopicCategory.objects.filter(parent_category__code=current_tab)
        if current_tab == 'tech':
            topic_obj = Topic.objects.select_related('author', 'category').all().order_by(
                'category__category_type', '-add_time')[0:30]
        else:
            topic_obj = Topic.objects.select_related('author', 'category').filter(
                category__parent_category__code=current_tab).order_by('category__category_type', '-add_time')[0:30]
        return render(request, 'topic/index.html', locals())
'''
class UploadFile(View):
    @method_decorator(login_auth)
    def dispatch(self, request, *args, **kwargs):
        return super(UploadFile, self).dispatch(request, *args, **kwargs)

    def get(self, request):
        # 获取
        user_obj = User.objects.filter(id=request.session.get('user_info')['uid']).first()
        return render(request, 'user/new.html', locals())

    def post(self, request):
        has_error = True
        # 验证
        user_obj = User.objects.filter(id=request.session.get('user_info')['uid']).first()
        obj = AvatarSettingsForm(request.POST, request.FILES)
        if obj.is_valid():
            upload_file = request.FILES['file']
            # 判断文件大小，小于10M才可以
            if upload_file.size <= 10 * 1024 * 1024:
                file_path = save_upload_file(upload_file)
                user_obj.avatar = avatar_path
                # 保存
                user_obj.save()
                #request.session['topic']['avatar'] = user_obj.avatar
                has_error = False
            else:
                avatar_size_error = "文件不能大于10M"
        return render(request, 'user/setting_avatar.html', locals())
'''


class NewTopicView(View):
    @method_decorator(login_auth)
    def dispatch(self, request, *args, **kwargs):
        return super(NewTopicView, self).dispatch(request, *args, **kwargs)

    def get(self, request):
        #get不能获取内容，无法进行甄别from合法性
        #obj = CheckNodeForm(request.GET)
        # if obj.is_valid():
        #     topic_node_code = obj.cleaned_data['topic_node_code']
        #     node_obj = TopicCategory.objects.filter(code=topic_node_code, category_type=2).first()
        #     return render(request, 'topic/new.html', locals())
        if UserProfile.objects.filter(groups__name="超级用户", id=request.session.get('user_info')['uid']):
            node_obj = TopicCategory.objects.filter()
        else:
            node_obj = TopicCategory.objects.filter(category_type=2)
        return render(request, 'topic/new.html', locals())

    def post(self, request):
        has_error = True
        #超级用户不必判断node类别
        if UserProfile.objects.filter(groups__name="超级用户", id=request.session.get('user_info')['uid']):
            obj = SuperNewTopicForm(request.POST)
        else:
            obj = NewTopicForm(request.POST)
        if obj.is_valid():
            has_error = False
            upload_file = request.FILES.getlist('myfile')
            # 判断文件大小，小于10M才可以
            if upload_file:
                for f in upload_file:
                    if f.size <= 10 * 1024 * 1024:
                        file_name = f
                        file_path = save_upload_file(f)
                        has_error = False
                    else:
                        has_error = True
                        upload_size_error = "文件不能大于10M"
                        if UserProfile.objects.filter(groups__name="超级用户", id=request.session.get('user_info')['uid']):
                            node_obj = TopicCategory.objects.filter()
                        else:
                            node_obj = TopicCategory.objects.filter(category_type=2)
                        return render(request, 'topic/new.html', locals())
            else:
                file_name = 'null'
                file_path = 'null'
            title = obj.cleaned_data['title']
            content = obj.cleaned_data['content']
            topic_node = obj.cleaned_data['topic_node']
            # 生成唯一随机码
            topic_sn = gender_topic_sn()
            # 过滤xss markdown转换
            title = bleach.clean(title)
            markdown_content = markdown.markdown(content, format="xhtml5", extensions=exts)
            markdown_content = bleach.clean(markdown_content, tags=markdown_tags, attributes=markdown_attrs)
            # 保存
            topic_obj = Topic.objects.create(author_id=request.session.get('user_info')['uid'], title=title,
                                             markdown_content=markdown_content,
                                             file=file_path,
                                             file_name=file_name,
                                             category_id=topic_node,
                                             topic_sn=topic_sn)

            # 使用F 自增此字段 更新Topic 所属的node 的统计数
            TopicCategory.objects.filter(id=topic_node, category_type=2).update(count_topic=F('count_topic') + 1)

            # 发帖，余额变动
            update_balance(request, update_type='create', obj=topic_obj)
            return redirect(reverse('topic', args=(topic_sn,)))
        node_obj = TopicCategory.objects.filter(category_type=2)
        return render(request, 'topic/new.html', locals())


class RecentView(View):
    @method_decorator(login_auth)
    def dispatch(self, request, *args, **kwargs):
        return super(RecentView, self).dispatch(request, *args, **kwargs)

    def get(self, request):
        current_page = request.GET.get('p', '1')
        current_page = int(current_page)
        topic_obj = Topic.objects.select_related('author', 'category').all().order_by('-add_time')
        page_obj = Paginator(current_page, topic_obj.count())
        topic_obj = topic_obj[page_obj.start:page_obj.end]
        page_str = page_obj.page_str(reverse('recent') + '?')
        return render(request, 'topic/recent.html', locals())


class NodeView(View):
    def get(self, request, node_code):
        current_page = request.GET.get('p', '1')
        current_page = int(current_page)
        try:
            node_obj = TopicCategory.objects.get(code=node_code)
            if request.session.get('user_info'):
                node_obj.favorite = FavoriteNode.objects.values_list('favorite').filter(
                    user_id=request.session.get('user_info')['uid'],
                    node=node_obj).first()
            topic_obj = Topic.objects.select_related('author', 'category').filter(category=node_obj).order_by(
                '-add_time')
            page_obj = Paginator(current_page, topic_obj.count())
            topic_obj = topic_obj[page_obj.start:page_obj.end]
            page_str = page_obj.page_str(reverse('node', args=(node_code,)) + '?')
            return render(request, 'topic/node.html', locals())
        except TopicCategory.DoesNotExist:
            raise Http404("node does not exist")

class TabNodeView(View):
    def get(self, request, node_code):
        current_page = request.GET.get('p', '1')
        current_page = int(current_page)
        try:
            node_obj = TopicCategory.objects.get(code=node_code)
            if request.session.get('user_info'):
                node_obj.favorite = FavoriteNode.objects.values_list('favorite').filter(
                    user_id=request.session.get('user_info')['uid'],
                    node=node_obj).first()
            topic_obj = Topic.objects.select_related('author', 'category').filter(category=node_obj).order_by(
                '-add_time')
            page_obj = Paginator(current_page, topic_obj.count())
            topic_obj = topic_obj[page_obj.start:page_obj.end]
            page_str = page_obj.page_str(reverse('node', args=(node_code,)) + '?')
            return render(request, 'topic/node.html', locals())
        except TopicCategory.DoesNotExist:
            raise Http404("node does not exist")


class NodeLinkView(View):
    def get(self, request, node_code):
        current_page = request.GET.get('p', '1')
        current_page = int(current_page)
        try:
            node_obj = TopicCategory.objects.get(code=node_code)
            if request.session.get('user_info'):
                node_obj.favorite = FavoriteNode.objects.values_list('favorite').filter(
                    user_id=request.session.get('user_info')['uid'],
                    node=node_obj).first()
            node_link_obj = NodeLink.objects.select_related('author').filter(
                category=node_obj).order_by('-add_time')
            page_obj = Paginator(current_page, node_link_obj.count())
            node_link_obj = node_link_obj[page_obj.start:page_obj.end]
            page_str = page_obj.page_str(reverse('node_link', args=(node_code,)) + '?')
            return render(request, 'topic/node_link.html', locals())
        except TopicCategory.DoesNotExist:
            raise Http404("node does not exist")


class TopicView(View):
    def get(self, request, topic_sn):
        try:
            topic_obj = Topic.objects.get(topic_sn=topic_sn)
            # 添加其他属性
            topic_obj.like_num = TopicVote.objects.filter(vote=1, topic=topic_obj).count()
            topic_obj.dislike_num = TopicVote.objects.filter(vote=0, topic=topic_obj).count()
            topic_obj.favorite_num = TopicVote.objects.filter(favorite=1, topic=topic_obj).count()
            comments_obj = Comments.objects.select_related('author').filter(topic=topic_obj)
            now = datetime.now()
            if request.session.get('user_info'):
                topic_obj.thanks = TopicVote.objects.values_list('thanks').filter(topic=topic_obj,
                                                                                  user_id=
                                                                                  request.session.get('user_info')[
                                                                                      'uid']).first()
                topic_obj.favorite = TopicVote.objects.values_list('favorite').filter(topic=topic_obj,
                                                                                      user_id=
                                                                                      request.session.get('user_info')[
                                                                                          'uid']).first()
            # 使用F 自增此字段 增加一次阅读数量
            Topic.objects.filter(topic_sn=topic_sn).update(click_num=F('click_num') + 1)
            return render(request, 'topic/topic.html', locals())
        except Topic.DoesNotExist:
            raise Http404("topic does not exist")

    @method_decorator(login_auth)
    def post(self, request, topic_sn):
        content = request.POST.get('content', None)
        if content is not None:
            try:
                topic_obj = Topic.objects.select_related('author').get(topic_sn=topic_sn)
                content = bleach.clean(content)
                comments_obj = Comments.objects.create(topic=topic_obj,
                                                       author_id=request.session.get('user_info')['uid'],
                                                       content=content)
                # 当前Topic 评论数 +1 使用F
                topic_obj.comment_num = F('comment_num') + 1
                # 修改当前Topic 最后评论信息
                topic_obj.last_comment_time = comments_obj.add_time
                topic_obj.last_comment_user = request.session.get('user_info')['username']
                topic_obj.save()
                # 发评论，对应余额变动 主题作者收到奖励，发回复者减去奖励
                # 不是当前topic作者才会有变动
                if topic_obj.author_id != request.session.get('user_info')['uid']:
                    update_balance(request, update_type='reply', obj=topic_obj)
                    update_balance(request, update_type='reply_recv', obj=topic_obj)
                return redirect(reverse('topic', args=(topic_sn,)))
            except Topic.DoesNotExist:
                raise Http404("topic does not exist")


class MarkdownPreView(View):
    @method_decorator(login_auth)
    def dispatch(self, request, *args, **kwargs):
        return super(MarkdownPreView, self).dispatch(request, *args, **kwargs)

    def post(self, request):
        obj = MarkdownPreForm(request.POST)
        if obj.is_valid():
            md = obj.cleaned_data['md']
            # 转为markdown格式
            md_html = markdown.markdown(md, format="xhtml5", extensions=exts)
            # 清理不安全的标签
            md_html = bleach.clean(md_html, tags=markdown_tags, attributes=markdown_attrs)
            return HttpResponse(md_html)

        return HttpResponse('')


class MyFavoriteNodeView(View):
    @method_decorator(login_auth)
    def dispatch(self, request, *args, **kwargs):
        return super(MyFavoriteNodeView, self).dispatch(request, *args, **kwargs)

    def get(self, request):
        my_favorite_obj = FavoriteNode.objects.select_related('node').filter(favorite=1,
                                                                             user_id=request.session.get('user_info')[
                                                                                 'uid']).order_by('-add_time')
        return render(request, 'topic/my_node.html', locals())


class MyFavoriteTopicView(View):
    @method_decorator(login_auth)
    def dispatch(self, request, *args, **kwargs):
        return super(MyFavoriteTopicView, self).dispatch(request, *args, **kwargs)

    def get(self, request):
        my_favorite_obj = TopicVote.objects.select_related('topic__author', 'topic__category').filter(
            favorite=1,
            user_id=request.session.get('user_info')['uid']).order_by('-add_time')

        return render(request, 'topic/my_topic.html', locals())


class MyFollowingView(View):
    @method_decorator(login_auth)
    def dispatch(self, request, *args, **kwargs):
        return super(MyFollowingView, self).dispatch(request, *args, **kwargs)

    def get(self, request):
        # 获取当前我正在关注的用户的QuerySet  判断 is_following  是不是 1
        my_following_obj = UserFollowing.objects.select_related('following').filter(
            user_id=request.session.get('user_info')['uid'],
            is_following=1)

        # 设定一个列表，存放查询到的所收藏的用户的id
        following_user_id = []
        # 把id 加入列表
        for obj in my_following_obj:
            following_user_id.append(obj.following.id)
        # 使用in查询用户id在所关注的用户的主题
        following_topic_obj = Topic.objects.select_related('category', 'author').filter(
            author_id__in=following_user_id).order_by('-add_time')

        return render(request, 'topic/my_following.html', locals())

def download(request, slug):
    the_file_name = slug
    file_path = Topic.objects.get(file_name=the_file_name).file
    file = file_path.open(mode='rb')
    response = FileResponse(file)
    response['Content-Type'] = 'application/octet-stream'
    response['Content-Disposition'] = 'attachment;filename="{0}"'.format(the_file_name)
    return response


def readFile(filename, chunk_size=512):
    with open(filename, 'rb') as f:
        while True:
            c = f.read(chunk_size)
            if c:
                yield c
            else:
                break

class DownloadView(View):
    def get(self, request, filename):
        Topic.objects.filter()
        print(request.GET)
        return HttpResponse('download')