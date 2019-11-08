#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author  : Aprsun
# @Time    : 2019/10


import os
import requests
import re
import time
import datetime
import pandas as pd
import smtplib
from email.mime.multipart import MIMEMultipart   # 构建邮件头信息
from email.mime.text import MIMEText    # 构建邮件正文
from email.header import Header    # 构建邮件标题
from email.utils import formataddr    # 格式化发件人地址

def GetUrls(page):
    """    
    获取 url 写入列表 urls
    """
    url_temp = 'http://vip.stock.finance.sina.com.cn/quotes_service/api/json_v2.php/Market_Center.getHQNodeData?page={}&num=80&sort=symbol&asc=1&node=hs_a&symbol=&_s_r_a=page'
    urls = []
    for i in range(1,page+1):
        url = url_temp.format(i)
        response = requests.get(url)
        urls.append(url)
        
#         if response.status_code == 200:
#             urls.append(url)
#         else:
#             print ('error:'+str(time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time())))+' page={}'.format(i))
#             continue
        
        time.sleep(2)
    print (str(time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time())))+' GetUrl succeed')
    return urls

def GetData(urls):
    """
    对爬取到的数据 进行处理 
    """
    value_list = []
    for url in urls:
        html = requests.get(url)
        rawdata = html.text[1:-1].replace(',{','\n').replace('{','').replace('}','').replace('"','')
        data_list = rawdata.split('\n')
        key_list = re.findall(r'([a-z]+):',data_list[0])
        #print (key_list)
        for i in range(len(data_list)):
            value_tup = re.findall(".*symbol:(.*),code:(.*),name:(.*),trade:(.*),pricechange:(.*),changepercent:(.*),buy:(.*),sell:(.*),settlement:(.*),open:(.*),high:(.*),low:(.*),volume:(.*),amount:(.*),ticktime:(.*),per:(.*),pb:(.*),mktcap:(.*),nmc:(.*),turnoverratio:(.*)",data_list[i])
            value_tmp = list(value_tup[0])
            #print(value_list)
            value_list.append(value_tmp)
    print (str(time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time())))+' GetData succeed')    
    return key_list,value_list

def GetStock(key_list,value_list):
    """
    创建 dataframe 并在 dataframe 上对数据进行进一步处理
    """
    stock = pd.DataFrame(value_list,columns = key_list )
    #stock.loc[:,['ticktime']] = str(time.strftime("%Y%m%d"))   # 修改 ticktime 的值为日期
    day = str(time.strftime("%Y%m%d"))    # 格式化日期
    stock['ticktime'] = day + ' ' + stock['ticktime']    # 在 ticktime 列原本的时间之前 加上日期 
    region = stock.symbol.astype(str).str[0:2]    # 提取symbol列前两个字符 以区分沪深两个股市
    shanghai_stock = stock.loc[region == 'sh']  
    date =str(time.strftime("%Y%m%d"))
    file_name = ''.join(('shanghai_stock_',date))
    shanghai_stock.to_csv('{}.csv'.format(file_name),index=False,encoding = "GBK")   # 保存 shanghai_stock.csv 留作备份
    print (str(time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time())))+' GetStock succeed') 
    return shanghai_stock

def GetLimitup(shanghai_stock):
    """
    在 shanghai_stock 的基础上 筛选出涨停（价格变化比率大于等于10%）的股票 
    为了方便追踪相应的股票 为每支股票添加 url 列 指向股票详情页
    """
    shanghai_stock['changepercent'] = pd.to_numeric(shanghai_stock['changepercent'])    # 把 ‘changepercent’列 转化为数字型 方便后续操作
    shanghai_limitup =shanghai_stock.loc[shanghai_stock['changepercent'] >= 10]    # 筛选出价格变化比率大于等于 10% 的股票 另存为 shanghai_limitup
    symbols = shanghai_limitup['symbol'].values    # 取 symbol 列 生成每支股票相应的详情页 url
    for i in symbols:
        stockurl = 'https://finance.sina.com.cn/realstock/company/{}/nc.shtml'
        shanghai_limitup.loc[shanghai_limitup['symbol'] == i ,'url'] = stockurl.format(i)
    date =str(time.strftime("%Y%m%d"))
    file_name = ''.join(('shanghai_limitup_',date))
    shanghai_limitup.to_csv('{}.csv'.format(file_name),index=False,encoding = "GBK")
    print (str(time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time())))+' Get_limitup succeed') 
    return shanghai_limitup

    
def GetDate():
    """
    考虑到周一时需要和上周五的数据对比 所以对星期几进行判断 
    """
    today = datetime.date.today() 
    weekday=today.weekday()+1    # .weekday() 函数 周一返回 ‘0’周日返回‘6’为了方便认知 还是加上了1  
    if weekday == 1:    # 当今天是周一时 获取周五的日期
        yesterday = str(today - datetime.timedelta(days=3)).replace('-','')
    else:
        yesterday = str(today - datetime.timedelta(days=1)).replace('-','')
    return yesterday

def ReadCsv(yesterday):
    """
    读取今天和昨天的涨停股票数据
    """
    pd.set_option('max_colwidth', 200)    # 为了完整显示 url 调整列的最大宽度
    pd.set_option('colheader_justify', 'center')    # 保持列名居中
       
    tfilename = 'shanghai_limitup_'+ str(time.strftime("%Y%m%d"))
    today_limit = pd.read_csv("{}.csv".format(tfilename),encoding = "gbk")
    
    yfilename = 'shanghai_limitup_'+ yesterday
    coldstart = os.path.isfile("{}.csv".format(yfilename))    # 判断昨天的文件是否存在 
    
    if coldstart == False:
        todaylimit = today_limit[['code','name','buy','sell','url']].to_html()
        Continuouslimit = ('没有连续两天涨停的股票')
    else:
        yesterday_limit = pd.read_csv("{}.csv".format(yfilename),encoding = "gbk")  
        #shanghai_limitup['code'] = pd.to_numeric(shanghai_limitup['code'])
    
        if today_limit.empty:    # 考虑到有可能存在到收盘时没有涨停的股票 添加 if 判断
            todaylimit = ('今天没有涨停的股票')
            Continuouslimit = ('没有连续两天涨停的股票')
        else:
            Continuous_limit = pd.merge(yesterday_limit,today_limit, on = ['code','name','url'], how = 'inner')
            # 如果 dataframe today_limit 不为空 则根据 'code' 'name' 'url' 三列 合并 yesterday_limit 和 today_limit
            todaylimit = today_limit[['code','name','buy','sell','url']].to_html() # 将 today_limit 转化为 html 

            if Continuous_limit.empty:    # 判断合并后的 Continuous_limit 是否为空 如果不为空 转成 html
                Continuouslimit = ('没有连续两天涨停的股票')
            else:
                Continuouslimit = Continuous_limit[['code','name','url']].to_html()
    return todaylimit,Continuouslimit

def GetMsg(todaylimit,Continuouslimit):
    """
    生成加在邮件里发送的 html 信息
    """
    head = \
        """
        <head>
            <style type="text/css">
                table.dataframe {
                    font-family: verdana,arial,sans-serif;
                    font-size:11px;
                    color:#333333;
                    border-width: 1px;
                    border-color: #666666;
                    border-collapse: collapse;
                }
                table.dataframe th {
                    border-width: 1px;
                    padding: 8px;
                    border-style: solid;
                    border-color: #666666;
                    background-color: #dedede;
                }
                table.dataframe td {
                    border-width: 1px;
                    padding: 8px;
                    border-style: solid;
                    border-color: #666666;
                    background-color: #ffffff;
                }
            </style>
        </head>
        """
    body = \
        """
        <body>
            <div>
                <h2>今天涨停的股票：</h2>
                    {}
            </div>
            <div>
                <h2>连续涨停的股票：</h2>
                    {}
            </div>
        </body>
        """.format(todaylimit,Continuouslimit)
    
    html_msg = "<html>" + head + body + "</html>"
    return (html_msg)

def SendEmail(receivers,head,html_msg):
    """
    发邮件
    """
    smtp_server = 'smtp.qq.com'    # 邮件服务信息
    username = "xxxxxxxxxx@qq.com"    # 发件人
    password = 'xxxxxxxxxx'    # qq邮箱第三方服务的授权码
    
    sender = username
    receiver = receivers
    
    msg = MIMEMultipart('related')
    msg['From']=formataddr(["Heartless postman",sender]) 
    msg['Subject'] = Header(head)
    msg['To'] = ','.join(receiver)
    
    content_html = MIMEText(html_msg,"html","utf-8")
    msg.attach(content_html)
    
    #email_client = smtplib.SMTP(smtp_server，25)
    email_client = smtplib.SMTP_SSL(smtp_server，465)	
    # 在阿里云运行代码时 出现连接超时的情况 怀疑是防火墙的原因 
    email_client.login(username,password)
    email_client.sendmail(sender,receiver,msg.as_string())
    email_client.quit()

def Gather():
    """
    调用爬虫部分的函数
    """
    page = 47
    receivers = ['xxxxxxxxxx@qq.com','xxxxxxxxxx@xxx.com']    # 可能需要在垃圾箱里找一找 至少gmail是这样的
    try:
        urls = GetUrls(page)
        key_list, value_list = GetData(urls)
        shanghai_stock = GetStock(key_list,value_list)
        shanghai_limitup = GetLimitup(shanghai_stock)    
    except Exception as e:
        head = "Oops！Something went wrong"
        html_msg_tmp = str(time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time())))+' error:', repr(e)
        html_msg = html_msg_tmp[0]+html_msg_tmp[1]    # 因为上面的报错信息是个元组 所以拿出来 整成字符串
        SendEmail(receivers,head,html_msg)    # 报错发送邮件
        
def Postman():
    """
    调用发邮件部分的函数
    """
    receivers = ['xxxxxxxxxx@qq.com']
    head = "今日涨停"
    try:
        yesterday = GetDate()
        todaylimit,Continuouslimit = ReadCsv(yesterday)
        html_msg = GetMsg(todaylimit,Continuouslimit)
        SendEmail(receivers,head,html_msg)
        print ("邮件发送成功！")
    except Exception as e:
        head = "Oops！Something went wrong"
        html_msg_tmp = str(time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time())))+' error:', repr(e)
        html_msg = html_msg_tmp[0]+html_msg_tmp[1]
        SendEmail(receivers,head,html_msg)
        
if __name__ == '__main__':
    flagname = 'shanghai_limitup_'+ str(time.strftime("%Y%m%d"))    
    flag = os.path.isfile("{}.csv".format(flagname))    # 添加判断 是否已经存在当天的数据文件 如果已存在就不运行爬虫部分
    today = datetime.date.today()
    weekday=today.weekday()+1
    if weekday not in [6,7]:    # 考虑到周末休市 如果是双休日就不运行
        if flag == False:
            Gather()
            time.sleep(30)    # 这个地方得睡一会 不然文件来不及保存 会读不到今天的数据文件
            Postman()
        else:
            Postman()
    else:
        print("休市")