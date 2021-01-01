import re
import requests
import time
import threading
from hashlib import md5
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from lxml import etree

from model import Phone, Browser, User
from verificationUntils import CrackTouClick


class PhoneService:
    def __init__(self, url, phone_num):
        self.phone_dict = {}
        # 需要获取的页数
        page_num = phone_num // 8 + 1
        for i in range(1, page_num + 1):
            phone_d = Phone(url.format(i)).get_phone()
            self.phone_dict.update(phone_d)
    
    def get_phone_dict(self):
        return self.phone_dict

    @staticmethod
    def get_phone_code(detail_href):
        headers = {
            'Connection': 'Keep-Alive',
            'User-Agent': 'Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 5.1; Trident/4.0)',
        }
        url = 'https://www.yinsiduanxin.com' + detail_href
        res = requests.get(url, headers=headers)
        resp = res.content
        html = etree.HTML(resp)
        td = html.xpath('//tbody//tr//td//a[@href="/receive-sms-from/畅言普通话"]/../..//'
                        'td[@style="word-break:break-word;"]//text()')
        try:
            phone_code = re.search('\\d{6}', td[0]).group()
        except IndexError:
            phone_code = 0
        print('手机验证码为: ', phone_code)
        return phone_code


class ClttService:
    """
    普通话报名服务类
    """
    @staticmethod
    def sign_up(base_info, user, chaojiying, phone_touple):
        """
        普通话报名
        :base_info: 基本信息类实例
        :user: user实例
        :chaojiying: 超级鹰实例
        :phone_touple: 手机号
        """

        print(phone_touple[0])
        print(user.name + '  https://www.yinsiduanxin.com' + phone_touple[1])
        
        browser = Browser().getBrowser()  # 创建浏览器对象
        # browser.maximize_window()  # 窗口最大化
        browser.get(base_info['url'])  # 访问报名链接
        wait = WebDriverWait(browser, 600)  # 设置显示等待

        # 选择城市
        getCheckCity = wait.until( lambda browser: browser.find_elements_by_xpath('//li[@class="fl item"]'))
        for i in getCheckCity:
            # print(i.text)
            if i.text == base_info['city']:
                i.click()
                break

        # 选择测试时间
        wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'choose-time')))
        choose_time_js = '''
            function choose_time(){
            time_li = document.getElementsByClassName('choose-time')[0].getElementsByTagName('li');
            mycars = new Array();
            for(i=0; i < time_li.length; i++){
                mycars.push(i);
            }
            index = mycars.splice(Math.floor(Math.random()*mycars.length), 1)
            document.getElementsByClassName('choose-time')[0].getElementsByTagName('li')[index].getElementsByTagName('a')[0].click();
            while(document.getElementsByClassName('data-none')[0] != undefined && mycars.length != 0){//当剩余名额为零，重新选择测试时间
                index = mycars.splice(Math.floor(Math.random()*mycars.length), 1)
                document.getElementsByClassName('choose-time')[0].getElementsByTagName('li')[index].getElementsByTagName('a')[0].click();
            }
        }choose_time();
        '''
        browser.execute_script(choose_time_js)
        
        #  点击下一步 阅读报名须知
        wait.until(EC.element_to_be_clickable((By.ID, 'toReadNote'))).click()
        browser.execute_script('document.getElementById("toReadNote").click()')
        
        # 识别极验
        CrackTouClick(browser, wait, chaojiying).crack_touh_click(0, 4, user)

        #  点击下一步 填写报名信息
        wait.until(EC.element_to_be_clickable((By.ID, 'lastRead'))).click()

        # 上传图片
        if user.photo != '无':
            wait.until(EC.presence_of_element_located((By.NAME, 'file'))).send_keys(user.photo)   

        #  填写考生姓名
        wait.until(EC.presence_of_element_located((By.NAME, 'name'))).send_keys(user.name)

        #  选择性别
        if user.sex == '男':
            choose_sex_js = 'document.getElementsByName("gender")[0].parentElement.getElementsByTagName("i")[0].click()'
        else:  # 女
            choose_sex_js = 'document.getElementsByName("gender")[0].parentElement.getElementsByTagName("i")[1].click()'
        browser.execute_script(choose_sex_js)
        
        # 选择民族
        ClttService.choose_nation(browser, user.nation)

        # 身份证号
        wait.until(EC.presence_of_element_located((By.NAME, 'idcard'))).send_keys(user.idCard)
        
        # 从事职业
        js = 'document.getElementsByName("employment")[0].parentElement.getElementsByTagName("dd")[8].click()'
        browser.execute_script(js)

        # 所在单位
        wait.until(EC.presence_of_element_located((By.NAME, 'wunit'))).send_keys(user.address)

        # 联系电话
        wait.until(EC.presence_of_element_located((By.NAME, 'telcontact'))).send_keys(phone_touple[0])

        # 点击下一步 到发送验证码界面
        time.sleep(3)
        click_to_phone_code_page_js = 'document.getElementsByTagName("button")[2].click()'
        browser.execute_script(click_to_phone_code_page_js)

        # 点击发送验证码
        wait.until(EC.element_to_be_clickable((By.ID, 'portMessage'))).click()

        # 识别极验
        CrackTouClick(browser, wait, chaojiying).crack_touh_click(1, 4, user)
        
        # 对接接码平台填入验证码
        # TODO
        time.sleep(30)
        phone_code = PhoneService.get_phone_code(phone_touple[1])
        wait.until(EC.presence_of_element_located((By.NAME, 'title'))).send_keys(phone_code)

        # 提交报名
        wait.until(EC.element_to_be_clickable((By.ID, 'save'))).click()

    @staticmethod
    def choose_nation(browser, nation):
        """
        选择民族
        """
        choose_nation_js = '''
            function choose(nation){
                ddlist = document.getElementsByName('nation')[0].parentElement.getElementsByTagName('dd');
                for (i=0; i < 58; i++){
                    if(ddlist[i].textContent == nation){
                    ddlist = document.getElementsByName('nation')[0].parentElement.getElementsByTagName('dd')[i].click();break;
                }
            }
        } choose("''' + nation + '''")'''
        browser.execute_script(choose_nation_js)
            

class UserService:
    """
    客户服务类
    """
    def __init__(self):
        self.user_list = []

    def get_user(self, path):
        """
        获取客户信息
        """
        with open(path, 'r', encoding='utf-8') as f:
            for line in f.readlines():
                user_info1 = line.strip('\n')
                user_info2 = user_info1.split('#')
                # 装载用户信息
                user = User(user_info2[0], user_info2[1], user_info2[2], user_info2[3], photo=user_info2[4])
                self.user_list.append(user)
        return self.user_list


# if __name__ == '__main__':
    # PhoneService.get_phone_code('/china-phone-number/verification-code-16224457442.html')
