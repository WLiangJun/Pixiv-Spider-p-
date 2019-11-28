#_*_coding=utf-8_*_
# python 3.7
# kotori  QQ:450072402   微信：WLJ_450072402
# pixiv爬虫

from selenium import webdriver
from lxml import etree
import time
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from requests import session
import json
from requests.cookies import RequestsCookieJar
import os
from queue import Queue
import gc   #garba collector 内存管理
import logging  #保证session.get()  verify=False条件下不报警告
import threading

logging.captureWarnings(True) #忽略警告

se = session()
se.keep_alive = False  #防止访问数量过多，服务器关闭请求  SSL443错误方法3：：：貌似有效
global jpg_success_num, png_success_num, driver_exsit, C_Path
global driver, time_scroll,time_wait
jpg_success_num = 0
png_success_num = 0
driver_exsit = False
C_Path = ''  #用于存放当前py所在路径   SSL报错解决方法二：：：失败
time_scroll = 1
time_wait = 2

class Pixiv():
    artist_num = 0
    def __init__(self, dir = '', google_dir = '', ID =''):
        self.profile_dir = google_dir            #r'C:\Users\Mimikko\AppData\Local\Google\Chrome\User Data'  # Google数据保存地址  #谷歌路径
        # 设置Google数据位置，方便调用密码数据，避免登陆等
        self.base_url = 'https://www.pixiv.net'  #这里是很多超链接的前缀
        self.download_path = dir  #r'E:\多媒体\pyspider'
        self.headers = {
            'Referer': 'https://accounts.pixiv.net/login?lang=zh&source=pc&view_type=page&ref=wwwtop_accounts_index',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.108 Safari/537.36',
            'Accept-Language': "zh-CN,zh;q=0.9",
            'Connection':'close'  #1.防服务器报错一：：：：防止服务器443错误， 超过允许连接数量  貌似无效
        }
        self.artist_ID = ID  #后通过循环进行赋值
        self.next_page_exist = True   #默认存在下一页
        self.target_url = ''
        self.pages = 1
        self.page_main = ''
        self.artistor_title = ''   #用于创建画集文件夹
        self.current_dir = ''
        self.url_dic = {'img_url_que': Queue(maxsize=0), 'Referer_url_que': Queue(maxsize=0), 'Page_num_que': Queue(maxsize=0), 'Page_num_list': []}
        if self.artist_num == 0:
            self.root_path()
            print("支持Google浏览器78版本及以上！！！\n")
            print("\t测试全局变量：long_wait_time: {0}\tshort_wait_time: {1}".format(time_wait, time_scroll))
        self.picture_size = 0
        self.artist_num += 1


    def get_art_url(self):
        self.target_url = r"https://www.pixiv.net/member_illust.php?id=" + self.artist_ID

    def root_path(self):
        self.current_dir = os.getcwd()  #获取执行路径
        os.chdir(self.download_path)
        print("图片下载目录:{0}...".format(self.download_path))
        print("配置文件存放地址：{}...".format(self.current_dir))

    def change_down_path(self, sub_dir):
        path_dir = self.download_path + sub_dir
        if not os.path.exists(path_dir):
            os.makedirs(path_dir)
            print("{} 存放路径创建成功...".format(path_dir))
        os.chdir(path_dir)

    def config_requests(self):
        #从Google获取cookies配置requests
        cookies = driver.get_cookies()
        print("从se获取改变前的cookies:\n", se.cookies)
        try:
            with open(C_Path + r'\cookies.json', 'w') as fp:
                json.dump(cookies, fp)
        except:
            print("从chrome cookies存放失败！\n")
        #这里用cookies对象进行处理
        try:
            jar = RequestsCookieJar()
            with open(C_Path + r'\cookies.json', 'r') as fp:
                cookies = json.load(fp)
                for cookie in cookies:
                    jar.set(cookie['name'], cookie['value'])
        except:
            print("cookies读取失败！\n")
        se.cookies = jar  #配置session
        print("从se获取改变后的cookies:\n", se.cookies)

    def get_html(self):
        #获取第一页
        global driver
        self.target_url = "https://www.pixiv.net/member_illust.php?id=" + str(self.artist_ID)
        try:
            driver.get(self.target_url)  # 绕过有人机检查  anmi: https://www.pixiv.net/member_illust.php?id=212801   Hiten: 'https://www.pixiv.net/member_illust.php?id=490219'
            # self.pages += 1
            time.sleep(time_scroll)
            self.page_main = driver.current_url
            self.artistor_title = driver.title.strip(" - pixiv")
            if driver_exsit == False:
                self.config_requests()
                driver_exsit == True  #待cookies数据获得后将状态置为True：表浏览器已创建成功
        except:
            print("网页打开失败！\n")
        print("当前解析页title：\t{0}\n".format(self.artistor_title))
        print("当前解析主页网址：\t{0}\n".format(self.page_main))  #将每位画师的首页存放在page_main中

    def get_big_img(self, id):
        if ('250x250' in id) == True:
            # date_id = id.strip("https://i.pximg.net/c/250x250_80_a2/img-master")  # 头字符串切除
            # date_id = date_id.strip('_square1200.jpg')  #去尾
            # 原图url拼接 字符串替换
            # img_url = 'https://i.pximg.net/img-original' + date_id + '.jpg'  # 不能直接下载,还要考虑不是jpg格式的图
            if ('custom-thumb/' in id):
                img_url = str(id).replace("https://i.pximg.net/c/250x250_80_a2/custom-thumb",
                                          "https://i.pximg.net/img-original")
                img_url = img_url.replace("_custom1200.jpg", ".jpg")  # 默认转换成
            else:
                img_url = str(id).replace("https://i.pximg.net/c/250x250_80_a2/img-master", "https://i.pximg.net/img-original")
                img_url = img_url.replace("_square1200.jpg", ".jpg")   #默认转换成
            self.url_dic['img_url_que'].put(img_url)
            print("原url：\t",id)
            # print("截取后字符串：\t", date_id)
            print("拼接img_url:\t{0}".format(img_url))

    def get_img_ref_pageNum(self):
        #打印检查 html = etree.HTML(text)
        # s = etree.tostring(html).decode()
        page = driver.page_source
        dom = etree.HTML(page)
        # all_xml = dom.xpath("//ul[@class='_2WwRD0o _2WyzEUZ']")
        li_list = driver.find_elements_by_xpath("//ul[@class='_2WwRD0o _2WyzEUZ']//li")
        # print(li_list)
        for element in li_list:
            # print("li... \t", element.text)
            try:
                img_url = element.find_element_by_xpath(".//img[@src]").get_attribute('src')
                self.get_big_img(img_url)
            except:
                print("该li节点没有img_url...\n")
                continue
            try:
                referer_url = element.find_element_by_xpath(".//a[@class='sc-fzXfQp bNPARF']").get_attribute('href')
                self.url_dic['Referer_url_que'].put(referer_url)  #入队列
                print("referer_url: ", referer_url)
            except:
                print("该li节点没有referer_url...\n")
                continue
            try:
                pic_num = element.find_element_by_xpath(".//span[@class='sc-fzXfOx bAzGJX']").text
                self.url_dic['Page_num_que'].put(int(pic_num))
                self.url_dic['Page_num_list'].append(int(pic_num))
                print("pic_num:\t{0}\n".format(pic_num))
            except:
                self.url_dic['Page_num_que'].put(1)
                self.url_dic['Page_num_list'].append(1)
                print("该作品为单图集...\n")
                continue
        if li_list.__len__() == 0:
            self.next_page_exist = False
        else:
            self.pages += 1
            # print("更改后的页数：\t{0}\n".format(self.pages))
        # print("all_xml_ul:\n", all_xml)

    def get_pagesource(self):
        #用xpath解析
        """
        获取全页面待下载的大图打开链接  即：referer链接, 解析大图链接
        :return:
        """
        page = driver.page_source
        # print(page)  # y用xpath helper获取的img  url：//img[contains(@src,"")]/@src
        dom = etree.HTML(page)
        # self.get_img_ref_pageNum(dom)
        dom.xpath('//img[contains(@src,"")]/@src')
        img_urls = dom.xpath('//img[contains(@src,"")]/@src')
        print("获取图片数量：", len(img_urls))
        hrefs = driver.find_elements_by_xpath("//a[@class='sc-fzXfQp bNPARF']")  #灵机一动，好像可以作为图片的名字，啊哈哈
        # img_url_que = driver.find_elements_by_xpath("//div[@class='sc-fzXfPI fRnFme']")
        img_url_que = self.get_big_img(img_urls)
        # for img_ in img_url_que:
        #     print("driver.find_element_by_xpath获取元素referers：{0}\n".format(img_.text))
        for href in hrefs:
            href_url = href.get_attribute('href')
            self.url_dic['Referer_url_que'].put(href_url)
            # print("全局href_url-{0}：\n".format(i), href_url)
        # for img in img_url_que:
        #     img_url = img.find_element_by_xpath("//img[@*]").get_attribute('src')
        #     self.url_dic['img_url_que'].append(img_url)
        for num in range(self.url_dic['Referer_url_que'].__len__()):
            print("第{0}个referer网址：\t{1}".format(num, (self.url_dic['Referer_url_que'][num]).strip()))
            print("第{0}个img网址：\t{1}\n".format(num, (self.url_dic['img_url_que'][num]).strip()))
        if hrefs.__len__() == 0:
            self.next_page_exist = False
        else:
            self.pages += 1
        print("referer网址数: {0}， img_url网址数： {1}"
              .format(self.url_dic['Referer_url_que'].__len__(), self.url_dic['img_url_que'].__len__()))
        return hrefs

    def next_page(self):
        # print("页面跳转检查：\t{0}\n".format(self.pages))
        next_url = self.page_main + '&p=' + str(self.pages)
        print("next_url:\t ", next_url)
        print("浏览器即将获取到 {0} 页...:".format(self.pages), next_url)
        driver.get(next_url)
        # self.pages += 1

    def url_full_page(self):
        if self.pages == 1:
            self.get_html()  #访问首页
        page_scroll(7, time_scroll)
        # self.get_pagesource()
        self.get_img_ref_pageNum()
        # self.get_img_url(self.get_pagesource())

    def get_multi_img(self, img_url, referer_url, pic_num, pic_name, suffix):
        """
        1、jpg格式     2、png   3、master1200.jpg    4、master1200.png    5、下载完成、失败
        :param img_url:
        :param referer_url:
        :param pic_num:
        :param pic_name:
        :return:
        """
        global jpg_success_num, png_success_num
        for num in range(pic_num):  #默认jpg下载
            img_url = str(img_url)
            if not num == 0:
                if ".jpg" in img_url:
                    img_url = img_url.replace("_p{0}.jpg".format(num-1), "_p{0}.jpg".format(num))
                elif ".png" in img_url:
                    img_url = img_url.replace("_p{0}.png".format(num - 1), "_p{0}.png".format(num))
            print("\t\t\t开始尝试jpg文件下载...")
            print("获取网页：\t{0}".format(img_url))
            img_url_source = img_url  #暂时保存jpg  url供master1200下载使用
            if self.pic_exist(pic_name, num, suffix):
                continue
            else:
                try:
                    response = se.get(img_url, headers=self.headers, stream=True, verify=False)  #加verify防止SSL报错2:::有效，谨慎删除
                    print("\t\t\t\tresponse 状态：", response.status_code)
                    # if not response.status_code == 200:
                    #     raise IndexError
                except:
                        print("{0}_p{1}--->服务器请求失败，将重试{2}次请求...".format(pic_name,num, retry_num))
                        for i in range(retry_num):
                            time.sleep(0.3)
                            try:
                                response = se.get(img_url, headers=self.headers, stream=True, verify=False)
                                if response.status_code == 200:
                                    break
                            except:
                                pass
                # with closing(se.get(img_url, headers=self.headers, stream=True, verify=False)) as response:
                if int(response.status_code) == 200:  # 网页正常打开
                    jpg_success_num += 1
                    # img = response.content
                    self.download_only(response, img_url, pic_name, suffix, num)  #启动下载
                else:
                    print("\t\t\tjpg格式下载错误，尝试png...")
                    img_url = str(img_url).strip(".jpg") + ".png"
                    if self.pic_exist(pic_name, num, "png"):
                        continue
                    else:
                        try:
                            response = se.get(img_url, headers=self.headers, stream=True, verify=False)  #加verify防止SSL报错2:::有效，谨慎删除
                            print("\t\t\t\tresponse 状态：", response.status_code)
                            # if not response.status_code == 200:
                            #     raise IndexError
                        except:
                            print("{0}_p{1}--->服务器请求失败，将重试{2}次请求...".format(pic_name,num, retry_num))
                            for i in range(retry_num):
                                time.sleep(0.3)
                                try:
                                    response = se.get(img_url, headers=self.headers, stream=True, verify=False)
                                    if response.status_code == 200:
                                        break
                                except:
                                    pass
                        if int(response.status_code) == 200:  # 网页正常打开
                            png_success_num += 1
                            # img = response.content
                            self.download_only(response, img_url, pic_name, "png", num)  # 启动下载
                        else:
                            self.download_retry(img_url_source, pic_name, num)  # 打开失败，尝试其它情况


    def download_only(self, response, img_url, pic_name, suffix, num):
        #仅提供图片保存功能，即写入磁盘
        # 文件不存在，创建文件开始下载图片
        chunk_size = 1024 #每次最大请求字节数
        content_size = int(response.headers['content-length']) #获得最大请求字节
        data_count = 0
        with open('{0}_p{1}.{2}'.format(pic_name, num, suffix), 'ab') as f:
            for data in response.iter_content(chunk_size=chunk_size):  #一块一块下载
                f.write(data)
                data_count = data_count + len(data)
                now = (data_count / content_size) * 100  #计算下载进度
                print("\r\t%s:%s下载进度： %d%%(%.2f/%.2f)" % (self.artistor_title,'{0}_p{1}.{2}'.format(pic_name, num, suffix),
                                                               now, data_count / 1024, content_size / 1024), end=" ")  #\r是防止多次打印
            print("{0}\t下载成功...\n".format(img_url))

    def pic_exist(self, pic_name, num, suffix, master = ""):  #存在则跳过向服务器申请  pic_name, num, "_master1200", "jpg"
        if not master == '':
            pic_name = str(pic_name) + master
        if os.path.exists('{0}_p{1}.{2}'.format(pic_name, num, suffix)):  # 开始下载
            print("文件存在，跳过\t{0}_p{1}.{2}\t下载...\n".format(pic_name, num, suffix))
            return True
        else:
            return False

    def download_retry(self, img_url, pic_name, num):
        """
        这种下载针对最后一种master1200，最大分辨率为1200的图片
        :return:
        """
        global jpg_success_num, png_success_num
        print("尝试master1200.jpg下载...")
        img_url = str(img_url).replace("https://i.pximg.net/img-original", "https://i.pximg.net/img-master")  #换头
        img_url = img_url.replace(".jpg", "_master1200.jpg")
        if self.pic_exist(pic_name, num, "jpg", "_master1200"):
            pass
        else:
            try:
                response = se.get(img_url, headers=self.headers, stream=True, verify=False)  #加verify防止SSL报错2:::有效，谨慎删除
#             print("\t\t\t\tresponse 状态：", response.status_code)
            #  if not response.status_code == 200:
#                 #     raise IndexError
            except:
                        print("{0}_p{1}--->服务器请求失败，将重试{2}次请求...".format(pic_name,num, retry_num))
                        for i in range(retry_num):
                            time.sleep(0.3)
                            try:
                                response = se.get(img_url, headers=self.headers, stream=True, verify=False)
                                if response.status_code == 200:
                                    break
                            except:
                                pass
            if int(response.status_code) == 200:  # 网页正常打开
                jpg_success_num += 1
                # img = response.content
                self.download_only(response, img_url, pic_name + "_master1200", "jpg", num)  # 启动下载
            else:
                print("尝试master1200.png下载...")
                img_url = img_url.replace("_master1200.jpg", "_master1200.png")
                if self.pic_exist(pic_name, num, "png", "_master1200"):
                    pass
                else:
                    try:
                        response = se.get(img_url, headers=self.headers, stream=True, verify=False)  #加verify防止SSL报错2:::有效，谨慎删除
                        print("\t\t\t\tresponse 状态：", response.status_code)
                        # if not response.status_code == 200:
                        #     raise IndexError
                    except:
                        print("{0}:{1}_p{2}--->服务器请求失败，将重试{3}次请求...".format(self.artistor_title, pic_name, num, retry_num))
                        for i in range(retry_num):
                            time.sleep(0.3)
                            try:
                                response = se.get(img_url, headers=self.headers, stream=True, verify=False)
                                if response.status_code == 200:
                                    break
                            except:
                                pass
                    if int(response.status_code) == 200:  # 网页正常打开
                        png_success_num += 1
                        # img = response.content
                        self.download_only(response, img_url, pic_name + "_master1200", "png", num)  # 启动下载
                    else:
                        print("四种方法均下载失败...┭┮﹏┭┮")

    def img_download_req(self, url_dic):  #self.url_dic = {'img_url_que': [], 'Referer_url_que': [], 'Page_num_que': []}
        self.change_down_path(r'\\' + self.artistor_title)  #创建画师文件夹
        sum = 0
        for i in self.url_dic['Page_num_list']: #统计图片总数
            sum += i
        with open("{0}_当前总p数.txt".format(self.artistor_title), 'w') as op:
            op.write("截至下载时间，已上传p站{0}张图\n包括所有单图集和多图集...\n{1}ID：{2}".format(sum, self.artistor_title, self.artist_ID))
        print("画师 {0} 图集下载dir：\t{1}".format(self.artistor_title, os.getcwd()))  #存放路径
        print("\t\t\t开始下载...")
        while not (url_dic['Referer_url_que'].empty()):
            referer_url = url_dic['Referer_url_que'].get()
            pic_name = str(referer_url).strip(r"https://www.pixiv.net/artworks/")  #图片命名
            self.headers['Referer'] = referer_url  #无论哪种下载方式，referer都不变
            img_url = url_dic['img_url_que'].get()
            pic_num = url_dic['Page_num_que'].get()
            self.get_multi_img(img_url, referer_url, pic_num, pic_name, 'jpg')

    def Pixiv_Go(self):
        global driver_exsit
        self.url_full_page()
        while self.next_page_exist:
            print("存在下一页...")
            try:
                print("切换下一页...")
                self.next_page()  #切换下一页面
                self.url_full_page()
            except:
                print("遍历了 {0} 页,切换下一页失败...".format(self.pages))
        print("遍历Hiten {0} 页，已到页末...\n关闭webdriver模拟器".format(self.pages))
        #检查总的数量是否对应
        print("referer网址数:\t{0}， img_url网址数：\t{1}，多图作品集数量：\t{2}\n"
              .format(self.url_dic['Referer_url_que']._qsize(), self.url_dic['img_url_que']._qsize(),
                      not_zero_num(self.url_dic['Page_num_list'])))
        self.img_download_req(self.url_dic)  #可开启多线程进行下载
        print("\t\t\t\t{0} 已全部下载完成".format(self.artistor_title))
        print("\t\t\t\t剩余referer网址数:\t{0}\t， 剩余img_url网址数：\t{1}\t\n"
              .format(self.url_dic['Referer_url_que']._qsize(), self.url_dic['img_url_que']._qsize()))

def not_zero_num(list):
    num = 0
    print('pic_numss: ', list)
    for i in range(list.__len__()):
        if list[i] != 1:
            num += 1
    return num

def ini_config_read(c_path):
    dic = {}
    ID = []
    try:
        with open(c_path + "\\config.json", 'r') as conf:
            dic = json.load(conf)
    except:
        print("config.json 文件打开失败，请确认文件是否存在...")
    try:
        with open(c_path + "\\画师ID.txt", 'r') as ID_f:
            for line in ID_f:
                lines = str(line.strip()).split()
                try:
                    ID.append(lines[1])  #只选取画师id
                except:
                    pass
    except:
        print("画师ID.txt 文件打开失败，请确认文件是否存在...")
    return dic, ID

def page_scroll(ranges, Time):
    # 模拟滚动条到底部  模拟pagedown
    global driver
    for i in range(ranges):
        ActionChains(driver).send_keys(Keys.PAGE_DOWN).perform()
        time.sleep(Time)
    time.sleep(time_wait)

def Driver(profile_dir):
    #配置一次就行
    # driver = webdriver.Chrome()
    # prefs = {'profile.default_content_settings.popups': 0, 'download.default_directory': self.download_path}
    global driver
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument("user-data-dir=" + profile_dir)  # +os.path.abspath(profile_dir)  也行
    try:
        driver = webdriver.Chrome(chrome_options=chrome_options)
    except:
        print("请求失败，请检查chrome是否关闭！\n")

if __name__ == '__main__':
    C_Path = os.getcwd()
    dic_dir, ID = ini_config_read(C_Path)
    # print(dic_dir)
    # print(ID)
    time_scroll = int(dic_dir["time_scroll"])
    time_wait = int(dic_dir["time_wait"])
    retry_num = int(dic_dir['retry_num'])
    print("\tlong_wait_time: {0}\tshort_wait_time: {1}".format(time_wait, time_scroll))
    Driver(dic_dir["google_dir"])
    pixiv = Pixiv(dic_dir["download_dir"], dic_dir["google_dir"])
    for id in ID:
        if not id == '':
            pixiv.__init__(dic_dir["download_dir"], dic_dir["google_dir"], str(id))  #用户自定义下载路径，下载画师id，以及Google数据路径
            pixiv.Pixiv_Go()
    print("\njpg成功总数:\t{0}\tpng成功总数：\t{1}".format(jpg_success_num, png_success_num))
    driver.quit()
    del pixiv,driver,se, jpg_success_num, png_success_num
    gc.collect()  #可单独写内存清理函数  https://blog.csdn.net/jiangjiang_jian/article/details/79140742

