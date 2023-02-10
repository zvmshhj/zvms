from zvms.models import *
from zvms.apilib import api
from zvms.util import *
import zvms.tokenlib as tk


@api(rule='/user/check')
def check(token_data):
    '''检查登录状态'''
    return success('获取成功', token_data)


@api(rule='/user/login', method='POST', params='Login', response='UserLoginResponse', auth=Categ.NONE)
def login(id, pwd, token_data):
    '''登录'''
    user = User.query.get(id)
    if not user or user.pwd != pwd:
        return error('用户名或密码错误')
    return success('登录成功', token=tk.generate(**user.select('id', 'auth', cls_id='cls')))


@api(rule='/user/logout', method='POST')
def logout(token_data):
    '''登出'''
    tk.remove(token_data)
    return success('登出成功')


@api(rule='/user/search', params='SearchUsers')
def search_users(token_data, name=None, cls=None, auth=None):
    '''搜索用户'''
    if name:
        query = User.query.filter(User.name.like(f'%{name}%'))
    else:
        query = User.query
    if cls:
        if auth:
            def filter_(u): return u.cls_id == int(cls) or u.auth & int(auth)
        def filter_(u): return u.cls_id == int(cls)
    elif auth:
        def filter_(u): return u.auth & int(auth)
    else:
        def filter_(_): return True
    return success('获取成功', list_or_error(select(filter(filter_, query), 'id', 'name')))


@api(rule='/user/<int:id>', response='UserInfoResponse')
def get_user_info(id, token_data):
    '''获取一个用户的详细详细信息'''
    user = User.query.get_or_error(id)
    return success('获取成功', **user.select('name', 'auth', cls_id='cls'), clsName=user.cls.name)

@api(rule='/user/<int:id>/time', response='VolunteerTimeResponse')
def get_volunteer_time(id, token_data):
    '''获取一个用户(学生)的义工分'''
    return success('获取成功', User.query.get_or_error(id).select('inside', 'outside', 'large'))


@api(rule='/user/mod-pwd', method='POST', params='ModPwd')
def modify_password(old, neo, token_data):
    '''修改自己的密码'''
    if len(neo) != 32:
        return error('密码格式错误')
    user = User.query.get(token_data['id'])
    if user.pwd != old:
        return error('旧密码错误')
    user.pwd = neo
    return success('修改成功')


@api(rule='/user/change-class', method='POST', params='ChangeClass')
def change_class(cls, token_data):
    '''修改自己(老师)的班级'''
    User.query.get(token_data['id']).cls_id = cls
    return success('修改成功')


@api(rule='/user/create', method='POST', params='Users', auth=Categ.SYSTEM)
def create_user(users, token_data):
    '''创建用户'''
    for user in users:
        Class.query.get_or_error(user['cls'], '班级不存在')
        if len(user['pwd']) != 32:
            return error('密码格式错误')
        User(
            id=user['id'],
            name=user['name'],
            cls_id=user['cls'],
            auth=user['auth'],
            pwd=user['pwd'],
            exp=0,
            last_sign_date=datetime.date.today()
        ).insert()
    return success('创建成功')


@api(rule='/user/<int:id>/modify', method='POST', params='User', auth=Categ.SYSTEM)
def modify_user(id, name, cls, auth, token_data):
    '''修改用户信息'''
    Class.query.get_or_error(cls, '班级不存在')
    User.query.get_or_error(id, '用户不存在').update(
        name=name,
        cls_id=cls,
        auth=auth,
    )
    return success('修改成功')


@api(rule='/user/<int:id>/delete', method='POST', auth=Categ.SYSTEM)
def delete_user(id, token_data):
    '''删除用户'''
    User.query.filter_by(id=id).delete()
    return success('删除成功')
