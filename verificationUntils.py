import requests
from hashlib import md5
from io import BytesIO
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from PIL import Image
import time


class Chaojiying(object):
    def __init__(self, username, password, soft_id, kind):
        self.kind = kind
        self.username = username
        password =  password.encode("utf8")
        self.password = md5(password).hexdigest()
        self.soft_id = soft_id
        self.base_params = {
            'user': self.username,
            'pass2': self.password,
            'softid': self.soft_id,
        }
        self.headers = {
            'Connection': 'Keep-Alive',
            'User-Agent': 'Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 5.1; Trident/4.0)',
        }

    def post_pic(self, im, codetype):
        """
        im: 图片字节
        codetype: 题目类型 参考 http://www.chaojiying.com/price.html
        """
        params = {
            'codetype': codetype,
        }
        params.update(self.base_params)
        files = {'userfile': ('ccc.jpg', im)}
        r = requests.post('http://upload.chaojiying.net/Upload/Processing.php', data=params, files=files, headers=self.headers)
        return r.json()

    def report_error(self, im_id):
        """
        im_id:报错题目的图片ID
        """
        params = {
            'id': im_id,
        }
        params.update(self.base_params)
        r = requests.post('http://upload.chaojiying.net/Upload/ReportError.php', data=params, headers=self.headers)
        return r.json()


class CrackTouClick:
    """
    过验证码类
    """
    def __init__(self, browser, browser_wait, chaojiying):
        self.browser = browser
        self.wait = browser_wait
        self.chaojiying = chaojiying

    def judge_success(self, step):
        """
        判断是否验证成功
        """
        if step == 0:
            tip = self.wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'geetest_result_tip'))).get_attribute('textContent')
        else:
            tip = self.browser.execute_script('document.getElementsByClassName("geetest_result_tip")[1].textContent')
        if tip == '验证失败 请按提示重新操作':
            return False
        else:
            return True

    def get_touclick_element_one(self):
        """
        第一次极验，获取验证码图片对象
        :return: 图片元素
        """
        element = self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR,'.geetest_holder')))
        return element
    
    def get_touclick_element_two(self):
        """
        第二次极验，获取验证码图片对象
        :return: 图片元素
        """
        element = self.browser.find_elements_by_class_name('geetest_panel_next')[2]
        return element
    
    def get_position(self, step):
        """
        获取验证码位置
        :step: 极验的次序
        :return: 验证码位置元组
        """
        if step == 0:
            element = self.get_touclick_element_one()
        else:
            element = self.get_touclick_element_two()
        location = element.location
        size = element.size
        top, bottom, left, right = location['y'], location['y'] + size['height'], location['x'], location['x'] + size[
            'width']
        return (top, bottom, left, right)
 
    def get_screenshot(self):
        """
        获取网页截图
        :return: 截图对象
        """
        screenshot = self.browser.get_screenshot_as_png()
        screenshot = Image.open(BytesIO(screenshot))
        return screenshot
    
    def get_touclick_image(self, step, user, name='captcha.png'):
        """
        获取点触验证码图片
        :param name:
        :return: 图片对象
        """
        if step == 0:
            im = self.get_touclick_element_one()
        else:
            im = self.get_touclick_element_two()
        time.sleep(3)
        im.screenshot(user.name + 'captcha_.png')
        captcha = Image.open(user.name + 'captcha_.png')
        # 改变截图的大小 和原图一致
        captcha = captcha.resize((im.size['width'], im.size['height']))
        captcha.save(user.name + 'captcha_resize.png')
        return captcha

    def send_image_to_chaojiying(self, step, user):
        """
        超级鹰识别坐标
        : return:超级鹰返回的坐标
        """
        image = self.get_touclick_image(step, user)
        bytes_array = BytesIO()
        image.save(bytes_array, format='PNG')
        # 读取到图片
        result = self.chaojiying.post_pic(bytes_array.getvalue(), self.chaojiying.kind)
        return result

    def get_points(self, captcha_result):
        """
        解析识别结果
        :param captcha_result: 识别结果
        :return:转换后的结果
        """
        # 获取点击的坐标
        groups = captcha_result.get('pic_str').split('|')
        locations = [[int(number) for number in group.split(',')] for group in groups]
        return locations
 
    def touch_click_words(self, locations, step):
        """
        点击验证图片
        :param locations: 点击位置
        :return:
        """
        for location in locations:
            if step == 0:
                ActionChains(self.browser).move_to_element_with_offset(self.get_touclick_element_one(), location[0], 
                                                                                    location[1]).click().perform()
                time.sleep(1)
            else:
                ActionChains(self.browser).move_to_element_with_offset(self.get_touclick_element_two(), location[0],
                                                                                    location[1]).click().perform()
                time.sleep(1)
            
    
    def crack_touh_click(self, step, test_num, user):
        test_num -= 1
        if test_num == 0:
            print('客户：' + user.name + ' 二次极验未通过, 请人工点击验证码')
            exit()

        # 获取点击的位置
        result = self.send_image_to_chaojiying(step, user)
        # TODO
        self.chaojiying.report_error(result['pic_id'])

        locations = self.get_points(result)
        self.touch_click_words(locations, step)

        if step == 0:
            # 点击确定
            self.wait.until(EC.element_to_be_clickable((By.CLASS_NAME, 'geetest_commit'))).click()
            # 延时等待验证结果
            self.wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'geetest_up')))
        else:
            # 点击确定
            sure_click_js = 'document.getElementsByClassName("geetest_commit")[1].click()'
            self.browser.execute_script(sure_click_js)
            # 延时等待验证结果
            time.sleep(1)

        # 判断是否成功
        if self.judge_success(step):
            print('验证成功')
            self.chaojiying.report_error(result['pic_id'])
        else:  # 可能不成功 重来
            print('重新验证')
            self.chaojiying.report_error(result['pic_id'])
            # time.sleep(2)
            self.crack_touh_click(step, test_num, user)

