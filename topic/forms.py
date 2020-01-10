from django import forms
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from topic.models import TopicCategory

User = get_user_model()


def topic_node_validate(topic_node):
    if not TopicCategory.objects.filter(id=topic_node, category_type=2).first():
        raise ValidationError('标签不存在')

def super_topic_node_validate(topic_node):
    if not TopicCategory.objects.filter(id=topic_node).first():
        raise ValidationError('标签不存在')

def topic_node_code_validate(topic_node_code):
    if not TopicCategory.objects.filter(code=topic_node_code, category_type=2).first():
        raise ValidationError('标签不存在')



class NewTopicForm(forms.Form):
    title = forms.CharField(max_length=120, required=True,
                            error_messages={'required': '标题不能为空', 'max_length': '超过标题字符限定'})
    content = forms.CharField(max_length=20000, required=False,
                              error_messages={'max_length': '超过内容字符限定'})
    file = forms.CharField(max_length=10000, required=False,
                           error_messages={'none': '文件为空'})
    topic_node = forms.CharField(validators=[topic_node_validate, ], required=True,
                                 error_messages={'required': '标签不能为空'})

class SuperNewTopicForm(forms.Form):
    title = forms.CharField(max_length=120, required=True,
                            error_messages={'required': '标题不能为空', 'max_length': '超过标题字符限定'})
    content = forms.CharField(max_length=20000, required=False,
                              error_messages={'max_length': '超过内容字符限定'})
    file = forms.CharField(max_length=10000, required=False,
                           error_messages={'none': '文件为空'})
    topic_node = forms.CharField(validators=[super_topic_node_validate, ], required=True,
                                 error_messages={'required': '标签不能为空'})

class CheckNodeForm(forms.Form):
    topic_node_code = forms.CharField(validators=[topic_node_code_validate, ], required=True,
                                      error_messages={'required': '标签不能为空'})


class MarkdownPreForm(forms.Form):
    md = forms.CharField(max_length=20000, required=True,
                         error_messages={'required': '内容不能为空', 'max_length': '超过字符限定'})
