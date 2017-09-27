

import re, time, json, logging, hashlib, base64, asyncio

from coreweb import get, post

from models import User, Comment, Blog, next_id

from apis import *

from aiohttp import web

from config import configs

COOKIE_NAME = 'awesession'
_COOKIE_KEY = configs.session.secret

@get('/')
def index(request):
    summary = 'Lorem ipsum dolor sit amet, consectetur adipisicing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.'
    blogs = [
        Blog(id='1', name='Test Blog', summary=summary, created_at=time.time()-120),
        Blog(id='2', name='Something New', summary=summary, created_at=time.time()-3600),
        Blog(id='3', name='Learn Swift', summary=summary, created_at=time.time()-7200)
    ]
    return {
        '__template__': 'blogs.html',
        'blogs': blogs
    }

_RE_EMAIL = re.compile(r'^[a-z0-9\.\-\_]+\@[a-z0-9\-\_]+(\.[a-z0-9\-\_]+){1,4}$')
_RE_SHA1 = re.compile(r'^[0-9a-f]{40}$')


@post('/api/users')
async def api_register_users(*, email, name, passwd):
    if not name or not name.strip():
        raise APIValueError('name')
    if not email or not _RE_EMAIL.match(email):
        raise APIValueError('email')
    if not passwd or not _RE_SHA1.match(passwd):
        raise APIValueError('passwd')

    users = await User.findAll('email=?',[email])
    if len(users) > 0:
        raise APIError('register:failed','email','Email is already in use')

    uid = next_id()
    shal1_passwd = '%s:%s' %(uid, passwd)
    user = User(id=uid, name=name.strip(),email=email,passwd=hashlib.sha1(shal1_passwd.encode('utf-8')).hexdigest(),image=' ')
    await user.save()
    # make session cookie:
    r = web.Response()
    r.set_cookie(COOKIE_NAME,user2cookie(user, 86400), max_age=86400, httponly=True)
    user.passwd = '******'
    r.content_type='application/json'
    r.body = json.dumps(user, ensure_ascii=False).encode('utf-8')
    return r


@get('/register')
def register():
    return {
        '__template__' : 'register.html'
    }

@post('/api/authenticate')
async def authenticate(*, email, passwd):
    if not email:
        raise APIValueError('email','Invalid email')
    if not passwd:
        raise APIValueError('passwd','Invalid passwd')
    users = await User.findAll('email=?',[email])
    if len(users) == 0:
        raise APIValueError('email', 'Email not exist')
    user = users[0]
    sha1 = hashlib.sha1()
    sha1.update(user.id.encode('utf-8'))
    sha1.update(b':')
    sha1.update(passwd.encode('utf-8'))
    if user.passwd != sha1.hexdigest():
        raise APIValueError('passwd','Invalid passwd')

    # authenticate ok, set cookie:
    r = web.Response()
    r.set_cookie(COOKIE_NAME, user2cookie(user, 86400), max_age=86400, httponly=True)
    user.passwd = '******'
    r.content_type = 'application/json'
    r.body = json.dumps(user, ensure_ascii=False).encode('utf-8')
    return r


@get('/signin')
def signin():
    return {
        '__template__':'signin.html'
    }


def user2cookie(user, max_age):
    expires = str(int(time.time() + max_age))
    s = '%s-%s-%s-%s' %(user.id, user.passwd, expires, _COOKIE_KEY)
    L = [user.id, expires, hashlib.sha1(s.encode('utf-8')).hexdigest()]
    return '-'.join(L)

async def cookie2user(cookiestr):
    '''
    Parse cookie and load user if cookie is valid
    :param cookiestr:
    :return:
    '''
    if not cookiestr:
        return None
    try:
        L = cookiestr.split('-')
        if len(L) != 3:
            return None
        uid, expires, sh1 = L
        # check cooike is overtime
        if int(expires) < time.time():
            return None
        user = await User.find(uid)
        if not user:
            return None
        # check passwd
        s = '%s-%s-%s-%s' % (user.id, user.passwd, expires, _COOKIE_KEY)
        sh2 = hashlib.sha1(s.encode('utf-8')).hexdigest()
        if sh1 == sh2:
            user.passwd= '******'
            return user
        else:
            return None
    except Exception as e:
        logging.exception(e)
        return None

