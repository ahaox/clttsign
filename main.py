import threading
from multiprocessing.dummy import Pool
from service import ClttService, PhoneService, UserService
from verificationUntils import Chaojiying, CrackTouClick
from model import BaseInfo


# 超级鹰用户名、密码、软件ID(需要注册)
CHAOJIYING_USERNAME = 'XXXXXX'
CHAOJIYING_PASSWORD = 'XXXXXX'
CHAOJIYING_SOFT_ID = 'XXXXXX'
CHAOJIYING_KIND = 9004  # 验证码类型


def run(base_info, user_list, chaojiying, phone_dict):
    """
    将参数装进数据列表启动进程
    """
    # ClttService.sign_up函数的参数列表
    data_list = []  # 参数列表[(base_info, user, chaojiying, phone_touple), (base_info, user, chaojiying, phone_touple)....]
    phone_dict_items = phone_dict.items()
    for user, phone_touple in zip(user_list, phone_dict_items):
        data = (base_info, user, chaojiying, phone_touple)
        data_list.append(data)
    
    # 创建用户数量个进程
    pool = Pool(len(user_list))
    # 每个进程启动功能函数
    pool.map(sign_up, data_list)
    pool.close()
    pool.join()


def sign_up(data):
    # 调用报名
    ClttService.sign_up(data[0], data[1], data[2], data[3])


if __name__ == '__main__':
    # 普通话报名网址
    cltt_url = 'http://gzbm.cltt.org/pscweb/signUp.html'
    # 报名城市
    city = '贵阳市'

    # 手机号获取网址
    phone_url = 'https://www.yinsiduanxin.com/china-phone-number/page/{}.html'
    # 客户信息文件
    user_path = '普通话.txt'
    # 需要照片 格式：  张三#女#汉族#5115XXXXXXXXXXX#C:\\Users\\ahao\\Desktop\\WPS图片-修改尺寸.jpg
    # 不需要照片格式：  张三#女#汉族#5115XXXXXXXXXXX#无

    # 读取客户信息
    user_list = UserService().get_user(user_path)
    user_num = len(user_list)
    # 创建基本信息对象
    base_info = BaseInfo(cltt_url, city).get_base_info()
    # 创建手机验证码服务对象
    phoneService = PhoneService(phone_url, user_num)
    phone_dict = phoneService.get_phone_dict()
    # 创建超级鹰验证对象
    chaojiying = Chaojiying(CHAOJIYING_USERNAME, CHAOJIYING_PASSWORD, CHAOJIYING_SOFT_ID, CHAOJIYING_KIND)
    # 启用多进程报名服务
    run(base_info, user_list, chaojiying, phone_dict)
