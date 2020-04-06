import requests
import re
import pytesseract  # TODO: Maybe a better OCR works better
import time
import json
import os
import prettytable as pt
from PIL import Image
from bs4 import BeautifulSoup


class Crawler:
    Headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:73.0) Gecko/20100101 Firefox/73.0',
               'Connection': 'keep-alive'}
    form = {}

    def __init__(self):
        self.session = requests.session()
        self.getUserPass()

    # 用户输入账户密码
    def getUserPass(self):
        self.form['user'] = input('please input your jaccount:')
        self.form['pass'] = input('please input your password:')


    # 设置提交表单信息
    def setForm(self, page):
        soup = BeautifulSoup(page, 'lxml')
        self.form['sid'] = soup.findAll('input')[0].get('value')
        self.form['returl'] = soup.findAll('input')[1].get('value')
        self.form['se'] = soup.findAll('input')[2].get('value')
        self.form['v'] = soup.findAll('input')[3].get('value')
        self.form['uuid'] = soup.findAll('input')[4].get('value')
        self.form['client'] = soup.findAll('input')[5].get('value')
        self.form['captcha'] = self.getCaptcha()

    # 获取验证码并识别
    def getCaptcha(self):
        url = 'https://jaccount.sjtu.edu.cn/jaccount/captcha?uuid=' + self.form['uuid'] + '&t=' + str(
            round(time.time() * 1000))
        with open('./captcha.jfif', 'wb') as f:
            f.write(requests.get(url).content)
        return pytesseract.image_to_string(Image.open('./captcha.jfif')).replace(' ', '')

    # 登录
    def login(self):
        print("登陆中...")
        loginURL = 'https://i.sjtu.edu.cn/jaccountlogin'
        while True:
            r = requests.get(loginURL)
            self.setForm(r.text)
            self.Headers['Referer'] = r.url
            uloginURL = 'https://jaccount.sjtu.edu.cn/jaccount/ulogin'
            r = self.session.post(uloginURL, data=self.form, headers=self.Headers)
            if re.search('i.sjtu', r.url):  # 登陆成功
                break
        os.remove('./captcha.jfif')
        print("登陆成功！\n---------")
        return r.url

    # 获取课程表
    def getSchedule(self, res):
        url = 'https://i.sjtu.edu.cn/kbcx/xskbcx_cxXsKb.html?gnmkdm=index&su=' + re.split('su=', res)[-1]
        self.Headers['Referer'] = res
        form = {'xnm': '2019', 'xqm': '12'}
        res = self.session.post(url, headers=self.Headers, data=form)
        kbList = json.loads(res.text).get('kbList')
        self.outputSchedule(kbList)

    # 输出课程表
    def outputSchedule(self, L):
        tb = pt.PrettyTable()
        tb.field_names = ['Course name', 'Classroom', 'Time', 'Teacher']
        for c in L:
            tb.add_row([c['kcmc'], c['cdmc'], c['xqjmc'] + c['jc'] + '(' + c['zcd'] + ')', c['xm']])
        print(tb)

    # 获取成绩单
    def getTranscript(self, *args):
        url = 'https://i.sjtu.edu.cn/cjcx/cjcx_cxXsKcList.html?gnmkdm=N305005&su=' + re.split('su=', args[0])[-1]
        referer = 'https://i.sjtu.edu.cn/cjcx/cjcx_cxDgXsxmcj.html?gnmkdm=N305007&layout=default&su=' + re.split('su=', args[0])[-1]
        if len(args) == 1:
            xnm = input('请输入学年（例：2019，表示2019-2020学年）：')
            xqm = input('请输入学期（例：1，表示第1学期）：')
            if xqm == '1':
                xqm = '3'
            elif xqm == '2':
                xqm = '12'
            else:
                xqm = '16'
        else:
            xnm = args[1]
            xqm = args[2]
        self.Headers['Referer'] = referer
        form = {'xnm': xnm, 'xqm': xqm}
        res = self.session.post(url, data=form)
        transcript_list = json.loads(res.text).get('items')
        self.outputTranscript(transcript_list)

    # 默认
    def getTranscript_default(self, res):
        url = 'https://i.sjtu.edu.cn/cjcx/cjcx_cxXsKcList.html?gnmkdm=N305005&su=' + re.split('su=', res)[-1]
        referer = 'https://i.sjtu.edu.cn/cjcx/cjcx_cxDgXsxmcj.html?gnmkdm=N305007&layout=default&su=' + re.split('su=', res)[-1]
        self.Headers['Referer'] = referer
        form = {'xnm': '3', 'xqm': '2019'}
        res = self.session.post(url, data=form)
        transcript_list = json.loads(res.text).get('items')
        self.outputTranscript(transcript_list)

    # 输出成绩单
    def outputTranscript(self, L):
        tb = pt.PrettyTable()
        tb.field_names = ['Course name', 'Credits', 'Scores']
        for c in L:
            tb.add_row([c['kcmc'], c['xf'], c['zpcj']])
        print(tb)


def main():
    c = Crawler()
    res = c.login()

    while True:
        opcode = input('请输入操作（0表示退出，1表示查询当前学期课程表，2表示查询成绩单，3默认）：')
        if opcode == '0':
            break
        elif opcode == '1':
            c.getSchedule(res)
        elif opcode == '2':
            c.getTranscript(res)
        else:
            c.getSchedule(res)
            c.getTranscript(res, '2019', '3')


main()
