import requests
import json
import time
import hmac
import hashlib
import logging
import copy
from urllib import parse


def _init_request():
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
        logging.info(
            f'GET {args[0]} - {response.status_code} - {filter_code(response.text)}')
        return response

    def post(*args, **kwargs):
        response = _post(*args, **kwargs)
        logging.info(
            f'POST {args[0]} - {response.status_code} - {filter_code(response.text)}')
        return response

    # 替换 requests 中的方法
    requests.get = get
    requests.post = post


_init_request()


class API:
    # 获取推荐帖子url
    _recommand_url = "https://zonai.skland.com/api/v1/rec/index"
    # 获取文章详情url
    _get_item_url = "https://zonai.skland.com/api/v1/item/list"
    # 获取帖子评论url
    _get_comment_url = "https://zonai.skland.com/api/v1/comment/list-by-topic"
    # 获取未读消息数url
    _get_unread_count_url = "https://zonai.skland.com/api/v1/unread/count"
    # 获取未成年状态url
    _get_teenager_status_url = "https://zonai.skland.com/api/v1/user/teenager"
    # 签到url
    _sign_url = "https://zonai.skland.com/api/v1/game/attendance"
    # 动作url
    _action_url = "https://zonai.skland.com/api/v1/action/trigger"
    # 分享url
    _share_url = "https://zonai.skland.com/api/v1/score/share"
    # 发评论url
    _post_comment_url = "https://zonai.skland.com/api/v1/comment/post"
    # 发布帖子url
    _publish_url = "https://zonai.skland.com/api/v1/item/sub"
    # 删除帖子url
    _delete_article_url = "https://zonai.skland.com/api/v1/item/del"
    # 检票url
    _checkin_url = "https://zonai.skland.com/api/v1/score/checkin"
    # 版区得分任务列表url
    _score_tasks_url = "https://zonai.skland.com/api/v1/score/tasks"
    # 绑定的角色url
    _binding_url = "https://zonai.skland.com/api/v1/game/player/binding"
    # 验证码url
    _login_code_url = "https://as.hypergryph.com/general/v1/send_phone_code"
    # 验证码登录
    _token_phone_code_url = "https://as.hypergryph.com/user/auth/v2/token_by_phone_code"
    # 密码登录
    _token_password_url = "https://as.hypergryph.com/user/auth/v1/token_by_phone_password"
    # 使用token获取认证代码
    _grant_code_url = "https://as.hypergryph.com/user/oauth2/v2/grant"
    # 使用认证代码获取cred
    _cred_code_url = "https://zonai.skland.com/api/v1/user/auth/generate_cred_by_code"

    _app_code = '4ca99fa6b56cc2ba'

    _send_comment_base_param = {
        "comment": {
            "id": 0,
            "userId": 0,
            "level": 1,
            "itemId": 0,
            "itemUserId": 0,
            "parentUserId": 0,
            "replyToSubCommentId": 0,
            "replyToUserId": 0,
            "format": "{\"version\":0,\"data\":[{\"type\":\"paragraph\",\"contents\":[{\"type\":\"text\",\"contentId\":\"1\",\"bold\":false,\"underline\":0,\"italic\":false,\"foregroundColor\":\"#222222\"}]}]}",
            "status": 0,
            "imageListSlice": [],
            "operationStatus": 0,
            "auditStatus": 0,
            "sortWeight": 0,
            "createdAtTs": 0,
            "updatedAtTs": 0,
            "firstIpLocation": ""
        }
    }

    _regions_tag_id = {
        "1": {
            "gameId": 1,
            "cateId": 2,
            "tagIdsSlice": [
                474
            ]
        },
        "2": {
            "gameId": 2,
            "cateId": 8,
            "tagIdsSlice": [35]
        },
        "3": {
            "gameId": 3,
            "cateId": 11,
            "tagIdsSlice": [297]
        },
        "4": {
            "gameId": 4,
            "cateId": 19,
            "tagIdsSlice": [588]
        },
        "100": {
            "gameId": 100,
            "cateId": 6,
            "tagIdsSlice": [306]
        }
    }
    _noauth_header = {
        'User-Agent': 'Skland/1.4.1 (com.hypergryph.skland; build:100001014; Android 31; ) Okhttp/4.11.0',
        'Accept-Encoding': 'gzip',
        'Connection': 'close'
    }

    def __init__(self, _hyusr_api_token):
        self._header = {
            'User-Agent': 'Skland/1.4.1 (com.hypergryph.skland; build:100001014; Android 31; ) Okhttp/4.11.0',
            'Accept-Encoding': 'gzip',
            'Connection': 'close'
        }
        self._hypergryph_api_token = _hyusr_api_token
        self._grant_code = self._get_grant_code_by_token()
        self._cred = self._get_cred_by_grant_code()

        self._header["cred"] = self._cred["cred"]
        self._skland_api_token = self._cred["token"]

        self._test_login_status()

    def _test_login_status(self):
        try:
            self.get_score_tasks()
        except Exception as e:
            if "用户未登录" in str(e):
                raise Exception("用户登录态失效")

    def _get_grant_code_by_token(self):
        token = self._hypergryph_api_token

        response = requests.post(self._grant_code_url, json={
            'appCode': self._app_code,
            'token': token,
            'type': 0
        }, headers=self._header)
        resp = response.json()

        if response.status_code != 200:
            raise Exception(f'获取认证代码失败：{resp}')
        if resp.get('status') != 0:
            raise Exception(f'获取认证代码失败：{resp["msg"]}')
        return resp['data']['code']

    def _get_cred_by_grant_code(self):
        grant_code = self._grant_code

        resp = requests.post(self._cred_code_url, json={
            'code': grant_code,
            'kind': 1
        }, headers=self._noauth_header).json()
        if resp['code'] != 0:
            raise Exception(f'获取cred失败：{resp["message"]}')
        return resp['data']

    def _generate_signature(self, token: str, path, body_or_query):
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

        # 签名请求头一定要这个顺序，否则失败
        # timestamp是必填的,其它三个随便填,不要为none即可
        header_for_sign = {
            'platform': '',
            'timestamp': '',
            'dId': '',
            'vName': '1.4.1'  # 低于4.1会导致服务器不处理浏览帖子加经验事件
        }

        header_ca = json.loads(json.dumps(header_for_sign))
        header_ca['timestamp'] = t
        header_ca_str = json.dumps(header_ca, separators=(',', ':'))
        s = path + body_or_query + t + header_ca_str
        hex_s = hmac.new(token, s.encode('utf-8'), hashlib.sha256).hexdigest()
        md5 = hashlib.md5(hex_s.encode('utf-8')
                          ).hexdigest().encode('utf-8').decode('utf-8')
        logging.info(f'算出签名: {md5}')
        return md5, header_ca

    def _get_sign_header(self, url: str, method, body):
        h = json.loads(json.dumps(self._header))
        p = parse.urlparse(url)
        if method.lower() == 'get':
            h['sign'], header_ca = self._generate_signature(
                self._skland_api_token, p.path, p.query)
        else:
            h['sign'], header_ca = self._generate_signature(
                self._skland_api_token, p.path, json.dumps(body))
        for i in header_ca:
            h[i] = header_ca[i]

        # FIXME:可能可以放在别的地方，但是不敢改
        # 必须使用1.4以上的版本，服务端才能正确处理加经验事件
        h['vName'] = '1.4.1'
        h['vCode'] = '100401001'
        return h

    def get_score_tasks(self) -> list:
        url = f"{self._score_tasks_url}?"
        resp = requests.get(
            url, headers=self._get_sign_header(url, 'get', '')).json()
        if resp['code'] != 0:
            raise Exception(f'获取任务列表失败：{resp["message"]}')
        return resp["data"]["list"]

    def get_binding_list(self) -> list:
        v = []
        resp = requests.get(self._binding_url, headers=self._get_sign_header(
            self._binding_url, 'get', None)).json()

        if resp['code'] != 0:
            raise Exception(f"获取角色列表失败：{resp['message']}")
        for i in resp['data']['list']:
            if i.get('appCode') != 'arknights':
                continue
            v.extend(i.get('bindingList'))
        return v

    def get_unread_message_count() -> dict:
        raise NotImplementedError()

    def sign(self, character) -> list:
        body = {
            'gameId': 1,
            'uid': character.get('uid')
        }
        resp = requests.post(self._sign_url, headers=self._get_sign_header(
            self._sign_url, 'post', body), json=body).json()
        if resp['code'] != 0:
            raise Exception(
                f'角色{character.get("nickName")}({character.get("channelName")})签到失败：{resp.get("message")}')
        return resp['data']['awards']

    def checkin(self, region_code) -> None:
        body = {
            'gameId': region_code
        }
        resp = requests.post(self._checkin_url, headers=self._get_sign_header(
            self._checkin_url, 'post', body), json=body).json()
        if (resp['code'] != 0):
            raise Exception(f'在版区{region_code}检票失败：{resp.get("message")}')

    def get_comment(self, item_id) -> list:
        url = f"{self._get_comment_url}?parentId={item_id}&parentKind=item&sortType=1&pageToken=0&userId=0&pageSize=15&topId=0"
        resp = requests.get(
            url, headers=self._get_sign_header(url, 'get', '')).json()
        if (resp['code'] != 0):
            raise Exception(f"获取文章{item_id}的评论列表失败：{resp['message']}")
        return resp['data']['list']

    def like_comment(self, item_id) -> None:
        try:
            self._action_item(item_id, 11)
        except API._ExecActionToItemException as e:
            raise Exception(f"为{item_id}点赞失败：{e.origin_msg}")

    def like_article(self, item_id) -> None:
        try:
            self._action_item(item_id, 12)
        except API._ExecActionToItemException as e:
            raise Exception(f"为{item_id}点赞失败：{e.origin_msg}")

    def fav_article(self, item_id):
        try:
            self._action_item(item_id, 21)
        except API._ExecActionToItemException as e:
            raise Exception(f"收藏{item_id}失败：{e.origin_msg}")

    class _ExecActionToItemException(Exception):
        def __init__(self, msg):
            self.origin_msg = msg

    def _action_item(self, item_id, action_id):
        body = {
            'action': int(action_id),
            'objectId': int(item_id)
        }
        resp = requests.post(self._action_url, headers=self._get_sign_header(
            self._action_url, 'post', body), json=body).json()
        if (resp['code'] != 0):
            raise API._ExecActionToItemException(resp['message'])

    def get_recommend_articles(self, region_code) -> list:
        url = f"{self._recommand_url}?gameId={region_code}&cateId=17&sortType=1&pageToken=&pageSize=10"
        resp = requests.get(
            url, headers=self._get_sign_header(url, 'get', None)).json()
        if (resp['code'] != 0):
            raise Exception(f"在版区{region_code}获取推荐列表失败：{resp['message']}")
        return resp['data']['list']

    def get_item_detail(self, item_id) -> None:
        url = f"{self._get_item_url}?ids={item_id}&teenager=0"
        resp = requests.get(
            url, headers=self._get_sign_header(url, 'get', None)).json()
        if (resp['code'] != 0):
            raise Exception(f"获取{item_id}详情失败：{resp['message']}")
        return resp['data']

    def send_comment(self, article_id, content) -> str:
        param = copy.deepcopy(self._send_comment_base_param)
        param["comment"]["parentId"] = article_id
        param["comment"]["textSlice"] = [{"id": "1", "c": content}]

        resp = requests.post(self._post_comment_url, headers=self._get_sign_header(
            self._post_comment_url, 'post', param), json=param).json()
        if (resp['code'] != 0):
            raise Exception(
                f"向文章{article_id}发表评论“{content}”失败，原因：{resp['message']}")
        return resp['data']['comment']['id']

    def publish_article(self, title, content, region) -> str:
        param = {
            "item": {
                "origin": 2,
                "repost": 1,
                "downloadEnable": 1,
                "source": "",
                "title": title,
                "viewKind": 4,
                "caption": [
                    {
                        "type": "text",
                        "id": "1"
                    }
                ],
                "format": "{\"version\":0,\"data\":[{\"type\":\"paragraph\",\"contents\":[{\"type\":\"text\",\"contentId\":\"1\",\"bold\":false,\"underline\":0,\"italic\":false,\"foregroundColor\":\"#222222\"}]}]}",
                "imageCoverIndex": "",
                "linkSlice": [],
                "textSlice": [
                    {
                        "id": "1",
                        "c": content
                    }
                ],
                "bvSlice": [],
                "imageListSlice": []
            }
        }
        param["item"].update(self._regions_tag_id[str(region)])
        resp = requests.post(self._publish_url, headers=self._get_sign_header(
            self._publish_url, 'post', param), json=param).json()
        if (resp['code'] != 0):
            raise Exception(f"发布文章（{title}）失败：{resp['message']}")
        return resp["data"]["item"]["id"]

    def delete_article(self, item_id) -> None:
        body = {
            "id": item_id
        }
        resp = requests.post(self._delete_article_url, headers=self._get_sign_header(
            self._delete_article_url, 'post', body), json=body).json()
        if (resp['code'] != 0):
            raise Exception(f"删除文章{item_id}失败：{resp['message']}")

    def share(self, region) -> None:
        body = {
            'gameId': region
        }
        resp = requests.post(self._share_url, headers=self._get_sign_header(
            self._share_url, 'post', body), json=body).json()
        if (resp['code'] != 0):
            print(f"执行分享动作失败：{resp['message']}")

    @staticmethod
    def get_token_by_phone_and_password(phone: str, password: str) -> str:
        r = requests.post(API._token_password_url, json={
                          "phone": phone, "password": password}, headers=API._noauth_header).json()

        if r.get('status') != 0:
            raise Exception(f'获取账号{phone}的token失败：{r["msg"]}')
        return r['data']['token']

    @staticmethod
    def get_token_by_phone_and_code(phone: str, code: str) -> str:
        r = requests.post(API._token_phone_code_url, json={
                          "phone": phone, "code": code}, headers=API._noauth_header).json()

        if r.get('status') != 0:
            raise Exception(f'获取账号{phone}的token失败：{r["msg"]}')
        return r['data']['token']

    @staticmethod
    def request_code(phone: str) -> None:
        resp = requests.post(API._login_code_url, json={
                             'phone': phone, 'type': 2}, headers=API._noauth_header).json()
        if resp.get("status") != 0:
            raise Exception(f"向{phone}发送验证码失败：{resp['msg']}")

    pass
