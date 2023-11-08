import hashlib
import hmac
import json
import os.path
import time
import datetime
from getpass import getpass
import logging
from urllib import parse

import requests

from skalnd_api import API

from datetime import date

api:API
publish_params = {
    "1":{
        "gameId": 1,
        "cateId": 2,
        "tagIdsSlice": [
            474
        ]
    },
    "2":{
        "gameId":2,
        "cateId":8,
        "tagIdsSlice":[35]
    },
    "3":{
        "gameId":3,
        "cateId":11,
        "tagIdsSlice":[297]
    },
    "4":{
        "gameId":4,
        "cateId":19,
        "tagIdsSlice":[588]
    },
    "100":{
        "gameId":100,
        "cateId":6,
        "tagIdsSlice":[306]
    }
}

token_save_name = 'TOKEN.txt'
app_code = '4ca99fa6b56cc2ba'
token_env = os.environ.get('TOKEN')
sign_token = ''
header = {
    'cred': '',
    'User-Agent': 'Skland/1.0.1 (com.hypergryph.skland; build:100001014; Android 31; ) Okhttp/4.11.0',
    'Accept-Encoding': 'gzip',
    'Connection': 'close'
}
header_login = {
    'User-Agent': 'Skland/1.0.1 (com.hypergryph.skland; build:100001014; Android 31; ) Okhttp/4.11.0',
    'Accept-Encoding': 'gzip',
    'Connection': 'close'
}

# 签名请求头一定要这个顺序，否则失败
# timestamp是必填的,vName低于1.4.1会导致服务器不处理加经验事件,其它三个随便填,不要为none即可
header_for_sign = {
    'platform': 1,
    'timestamp': '',
    'dId': '',
    'vName': '1.4.1' 
}

# 获取推荐帖子url
recommand_url = "https://zonai.skland.com/api/v1/rec/index"
# 获取文章详情url
get_item_url = "https://zonai.skland.com/api/v1/item/list"
# 获取帖子评论url
get_comment_url = "https://zonai.skland.com/api/v1/comment/list-by-topic"
# 获取未读消息数url
get_unread_count_url = "https://zonai.skland.com/api/v1/unread/count"
# 获取未成年状态url
get_teenager_status_url = "https://zonai.skland.com/api/v1/user/teenager"
# 签到url
sign_url = "https://zonai.skland.com/api/v1/game/attendance"
# 动作url
action_url = "https://zonai.skland.com/api/v1/action/trigger"
# 分享url
share_url = "https://zonai.skland.com/api/v1/score/share"
# 发评论url
comment_url = "https://zonai.skland.com/api/v1/comment/post"
# 发布帖子url
publish_url = "https://zonai.skland.com/api/v1/item/sub"
# 删除帖子url
delete_article_url = "https://zonai.skland.com/api/v1/item/del"
# 检票url
checkin_url = "https://zonai.skland.com/api/v1/score/checkin"
# 绑定的角色url
binding_url = "https://zonai.skland.com/api/v1/game/player/binding"
# 验证码url
login_code_url = "https://as.hypergryph.com/general/v1/send_phone_code"
# 验证码登录
token_phone_code_url = "https://as.hypergryph.com/user/auth/v2/token_by_phone_code"
# 密码登录
token_password_url = "https://as.hypergryph.com/user/auth/v1/token_by_phone_password"
# 使用token获得认证代码
grant_code_url = "https://as.hypergryph.com/user/oauth2/v2/grant"
# 使用认证代码获得cred
cred_code_url = "https://zonai.skland.com/api/v1/user/auth/generate_cred_by_code"


def config_logger():
    current_date = date.today().strftime('%Y-%m-%d')
    if not os.path.exists('logs'):
        os.mkdir('logs')

    file_handler = logging.FileHandler(f'./logs/{current_date}.log', encoding='utf-8')
    file_handler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    logging.basicConfig(handlers=[file_handler])

    def filter_code(text):
        filter_key = ['code', 'cred', 'token']
        try:
            j = json.loads(text)
            if not j.get('data'):
                return text
            data = j['data']
            for i in filter_key:
                if i in data:
                    data[i] = '*****'
            return json.dumps(j, ensure_ascii=False)
        except:
            return text

    _get = requests.get
    _post = requests.post

    def get(*args, **kwargs):
        response = _get(*args, **kwargs)
        logging.info(f'GET {args[0]} - {response.status_code} - {filter_code(response.text)}')
        return response

    def post(*args, **kwargs):
        response = _post(*args, **kwargs)
        logging.info(f'POST {args[0]} - {response.status_code} - {filter_code(response.text)}')
        return response

    # 替换 requests 中的方法
    requests.get = get
    requests.post = post


def generate_signature(token: str, path, body_or_query):
    """
    获得签名头
    接口地址+方法为Get请求？用query否则用body+时间戳+ 请求头的四个重要参数（dId，platform，timestamp，vName）.toJSON()
    将此字符串做HMAC加密，算法为SHA-256，密钥token为请求cred接口会返回的一个token值
    再将加密后的字符串做MD5即得到sign
    :param token: 拿cred时候的token
    :param path: 请求路径（不包括网址）
    :param body_or_query: 如果是GET，则是它的query。POST则为它的body
    :return: 计算完毕的sign
    """
    # 总是说请勿修改设备时间，怕不是yj你的服务器有问题吧，所以这里特地-2
    t = str(int(time.time()) - 2)
    token = token.encode('utf-8')
    header_ca = json.loads(json.dumps(header_for_sign))
    header_ca['timestamp'] = t
    header_ca_str = json.dumps(header_ca, separators=(',', ':'))
    s = path + body_or_query + t + header_ca_str
    hex_s = hmac.new(token, s.encode('utf-8'), hashlib.sha256).hexdigest()
    md5 = hashlib.md5(hex_s.encode('utf-8')).hexdigest().encode('utf-8').decode('utf-8')
    logging.info(f'算出签名: {md5}')
    return md5, header_ca


def get_sign_header(url: str, method, body, old_header):
    h = json.loads(json.dumps(old_header))
    p = parse.urlparse(url)
    if method.lower() == 'get':
        h['sign'], header_ca = generate_signature(sign_token, p.path, p.query)
    else:
        h['sign'], header_ca = generate_signature(sign_token, p.path, json.dumps(body))
    for i in header_ca:
        h[i] = header_ca[i]
    h['vName'] = '1.4.1'
    h['vCode'] = '100401001'
    return h


def login_by_code():
    phone = input('请输入手机号码：')
    API.request_code()
    print(f"已向{phone}发送手机验证码")

    code = input("请输入手机验证码：")
    return API.get_token_by_phone_and_code(phone,code)


def login_by_token():
    token_code = input("请输入（登录森空岛电脑官网后请访问这个网址：https://web-api.skland.com/account/info/hg）:")
    return parse_user_token(token_code)


def parse_user_token(t):
    try:
        t = json.loads(t)
        return t['data']['content']
    except:
        pass
    return t


def login_by_password():
    phone = input('请输入手机号码：')
    password = getpass('请输入密码：')
    return API.get_token_by_phone_and_password(phone,password)



def do_sign():
    characters = api.get_binding_list()

    for i in characters:
        try:
            awards = api.sign(i)
            for j in awards:
                res = j['resource']
                print(
                    f'角色{i.get("nickName")}({i.get("channelName")})签到成功，获得了{res["name"]}×{j.get("count") or 1}'
                )
        except Exception as e:
            print(str(e))


def get_score_by_checkin(region):
    try:
        api.checkin(region)
        print(f'[版区{region}]检票成功')
    except Exception as e:
        print(f'[版区{region}]{str(e)}')


def get_score_by_read_articles_and_like(region):    
    rec = api.get_recommend_articles(region)

    total_liked = 0

    for arti in rec:
    
        itemid = arti['item']['id']
        title = arti['item']['title']

        try:
            api.get_item_detail(itemid)
            print(f"[版区{region}]阅读文章《{title}》成功")
        except Exception as e:
            print(str(e))
            pass

        if total_liked < 10:
            try:
                comment = api.get_comment(itemid)
                for c in comment:
                    try:
                        comment_id = c['meta']['comment']['id']
                        api.like_item(comment_id)
                        print(f"[版区{region}][文章{itemid}]点赞评论{comment_id}成功")
                        total_liked+=1
                    except Exception as e:
                        print(str(e))
            except Exception as e:
                print(str(e))

def get_score_by_publish_like_and_reply(region):
    articles = []
    for i in range(10):
        try:
            title = f"水水水{i}"
            i_id = api.publish_article(title,f"{datetime.datetime.now()}",region)
            articles.append(i_id)
            print(f"[版区{region}]发布文章《{title}》成功")
        except Exception as e:
            print(f"[版区{region}]{str(e)}")

    first_comments = []
    for i in range(6):
        comment = api.send_comment(articles[0],f"{datetime.datetime.now()}")
        first_comments.append(comment)
        print(f"[版区{region}][文章{articles[0]}]发布评论{comment}成功")

    helper_token_file = "HELPER_TOKEN.txt"
    if (os.path.exists(helper_token_file)):
        helper_token = read(helper_token_file)[0]
        helper_api = API(helper_token)

        for at in articles:
            try:
                helper_api.like_item(at)
                print(f"[版区{region}][文章{articles[0]}]小号点赞文章{at}成功")
            except Exception as e:
                print(f"[版区{region}]{str(e)}")

            try:
                helper_api.fav_article(at)
                print(f"[版区{region}][文章{articles[0]}]小号收藏文章{at}成功")
            except Exception as e:
                print(f"[版区{region}]{str(e)}")

            try:
                helper_api.send_comment(at,f"{datetime.datetime.now()}")
                print(f"[版区{region}][文章{articles[0]}]小号发送评论成功")
            except Exception as e:
                print(f"[版区{region}]{str(e)}")
        
        for comment in first_comments:
            try:
                helper_api.like_item(comment)
                print(f"[版区{region}][文章{articles[0]}]小号点赞评论{comment}成功")
            except Exception as e:
                print(f"[版区{region}]{str(e)}")
    
    for arti in articles:
        try:
            api.delete_article(arti)
            print(f"[版区{region}][文章{arti}]删除成功")
        except Exception as e:
            print(f"[版区{region}]{str(e)}")

    

def get_score_by_share(i):
    try:
        api.share(i)
        print(f"[版区{i}]执行分享文章动作成功")
    except Exception as e:
        print(f"[版区{i}]{str(e)}")
    


def do_get_score():
    region = [1,2,3,4,100]

    for i in region:
        get_score_by_checkin(i)
        get_score_by_share(i)
        get_score_by_read_articles_and_like(i)
        get_score_by_publish_like_and_reply(i)
        time.sleep(30) #等待一下，避免频繁
    pass

def save(token):
    with open(token_save_name, 'w') as f:
        f.write(token)
    print(
        f'您的鹰角网络通行证已经保存在{token_save_name}, 打开这个可以把它复制到云函数服务器上执行!\n如果需要再次运行，删除创建的这个文件即可')


def read(path):
    v = []
    with open(path, 'r', encoding='utf-8') as f:
        for i in f.readlines():
            i = i.strip()
            i and i not in v and v.append(i)
    return v


def read_from_env():
    v = []
    token_list = token_env.split(',')
    for i in token_list:
        i = i.strip()
        if i and i not in v:
            v.append(parse_user_token(i))
    print(f'从环境变量中读取到{len(v)}个token...')
    return v


def do_init():
    if token_env:
        print('使用环境变量里面的token')
        # 对于github action,不需要存储token,因为token在环境变量里
        return read_from_env()

    # 检测文件里是否有token
    if os.path.exists(token_save_name):
        v = read(token_save_name)
        if v:
            return v
    # 没有的话
    token = ''
    print("请输入你需要做什么：")
    print("1.使用用户名密码登录（非常推荐，但可能因为人机验证失败）")
    print("2.使用手机验证码登录（非常推荐，但可能因为人机验证失败）")
    print("3.手动输入鹰角网络通行证账号登录(推荐)")
    mode = input('请输入（1，2，3）：')
    if mode == '' or mode == '1':
        token = login_by_password()
    elif mode == '2':
        token = login_by_code()
    elif mode == '3':
        token = login_by_token()
    else:
        exit(-1)
    save(token)
    return [token]


def start():
    token = do_init()
    for t in token:
        try:
            global api
            api = API(t)

            do_sign()
            do_get_score()
        except Exception as ex:
            print(f'处理森空岛日常事务失败：{str(ex)}')
            logging.error('', exc_info=ex)
    print("处理森空岛日常事务完成！")

if __name__ == '__main__':
    print('本项目源代码仓库：https://github.com/xxyz30/skyland-auto-sign(已被github官方封禁)')
    print('https://gitee.com/FancyCabbage/skyland-auto-sign')
    config_logger()

    logging.info('=========starting==========')

    start_time = time.time()
    start()
    end_time = time.time()
    logging.info(f'complete with {(end_time - start_time) * 1000} ms')
    logging.info('===========ending============')
