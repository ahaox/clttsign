import requests
from lxml import etree
from selenium import webdriver


class User:
    """
    客户类
    """
    def __init__(self, name, sex, nation, idCard, phone=None, address='无', photo=None):
        """
        @param name: 姓名
        @param idCard: 身份证号
        @param sex: 性别 
        @param nation: 民族
        @param address: 地址
        @param photo: 照片
        @param phone: 手机号
        """
        self.name = name
        self.idCard = idCard
        self.sex = sex
        self.nation = nation
        self.address = address
        self.photo = photo
        self.phone = phone


class BaseInfo:
    """
    基本信息类
    """
    def __init__(self, url, city, station=None, time=None):
        """
        @param url: 报名地址
        @param city: 报名城市
        @param station: 测试站
        @param time: 测试时间
        """
        self.base_info = {'url': url, 'city': city, 'station': station, 'time': time}

    def get_base_info(self):
        return self.base_info


class Browser:
    """
    浏览器类
    """
    def __init__(self):
        # 创建浏览器对象
        option = webdriver.ChromeOptions()
        option.add_experimental_option('useAutomationExtension', False)
        option.add_experimental_option('excludeSwitches', ['enable-automation'])
        # 不自动关闭浏览器
        option.add_experimental_option("detach", True)
        self.browser = webdriver.Chrome(chrome_options=option)

    def getBrowser(self):
        """
        返回浏览器对象列表
        """
        return self.browser


class Phone:
    """
    手机号类
    """
    def __init__(self, url):
        self.phone = None
        self.code = None
        self.url = url
        self.headers = {
            'Connection': 'Keep-Alive',
            'User-Agent': 'Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 5.1; Trident/4.0)',
        }
    
    def get_phone(self):
        res = requests.get(url=self.url, headers=self.headers)
        resp = res.content
        # print(resp)
        html = etree.HTML(resp)
        # 获取手机号
        phone_l1 = html.xpath('//p[@title="点击接收短信验证码"]//a//text()')  # ['+86', ' 16532701568', '+86', ' 16532701568'....]
        phone_l2 = [x for x in phone_l1 if x != '+86']  # [' 16532701568', ' 16532701568', ' 16532701568', .....]
        phone_list = [x[1:] for x in phone_l2]  # ['16532701568', '16532701569', '17107703029']
        # 获取验证码详情页链接
        code_detial_page_href = html.xpath('//p[@title="点击接收短信验证码"]//a//@href')
        # {'phone': 'detail_href'....}
        phone_dict = dict(zip(phone_list, code_detial_page_href))
        return phone_dict

