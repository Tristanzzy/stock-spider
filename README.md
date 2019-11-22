# 依据涨停 进行选股

## 更新

- 2019/10/25 </br>

  本地手动运行成功 </br>

- 2019/10/26 </br>

  双休日同样可以运行 爬下来的数据为周五下午三点收盘时的数据 </br>

- 2019/11/21 </br>

  服务器部署，定时运行代码</br>

  


## 简介

​		偶然得知，如果一只股票连涨两天的话，那么它在第三天有大概率是赚的。所以打算实现每天定时爬取新浪财经上的个股信息，并将连涨两天的股票通过邮件的形式通知自己。

### 需要的库

```python
#!/usr/bin/python
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
```

​		此代码仅供学习与交流。

## 思路

### 需要实现的功能

- [x] 从新浪财经 < http://vip.stock.finance.sina.com.cn/mkt/#hs_a > 获取数据
- [x] 从获得的数据中筛选出涨停的股票 并实现邮件通知
- [x] 服务器部署，定时运行代码
- [ ] 对连续涨停的股票持续关注，直到涨跌幅出现负值

### 获取网址

​		首先，打开链接，可以看到下图的界面，位于上方的红框内是关于每个页面显示的信息数量及页数信息，另一个红框内的信息包括股票的代码、名称、涨跌幅、买入、卖出等内容，也就是我们需要从网站上爬取的数据。</br>

![website_1](/pic/website_1.png)

​		点击翻页，URL 并没有随之发生明显的改变。

![website_2](/pic/website_2.png)

</br>

​		再打开 Chrome 浏览器的开发者工具 在 XHR 那里， 可以看到另一个 Request URL</br>

</br>

​		形如： 

> http://vip.stock.finance.sina.com.cn/quotes_service/api/json_v2.php/Market_Center.getHQNodeData?page=1&num=80&sort=symbol&asc=1&node=hs_a&symbol=&_s_r_a=auto 

​		从这个 Request URL 上，就能很轻易的推测出其中一些参数的内容。</br>

- page 显而易见，就是页数；

- num 也就是每页显示的信息条数；

- sort 和 asc 则代表信息按照第一列的代码进行升序排序；

- node 的值为 hs_a 也就是代表着沪深A股的意思。

- 至于最后的 _s_r_a 就不是很明白是什么意思了，但问题不大</br>

  在得到 URL 之后，就可以着手准备获取数据了。

  

### 解析网页&获取数据



### 服务器部署

#### 1. 申请与服务器

这个我也没啥研究，之前用过阿里云，这次也选择在阿里云开了个服务器，系统选择的是Centos7。

#### 2. 安装 Python3 及 运行所需的第三方库

系统自带的 Python 版本是2.7，需要手动安装 Python3，升级 pip。

这里我就不多赘述了，网上找一下攻略就成。

#### 3. 定时运行

使用 MobaXterm 远程连接到服务器，把 Python 文件上传至服务器。

Linux 中一般是由 crond 来周期性的执行指令列表。

crontab基本操作命令：

```
crontab -u  user # 指定用户的 crontab 服务，一般由 root 用户运行
crontab -l # 显示某用户的 crontab 文件，如果不指定用户则显示当前用户的 crontab 文件内容
crontab -e # 编辑某用户的 crontab 文件，如果不指定用户则编辑当前用户的 crontab 文件内容
crontab -r # 删除某用户的 crontab 文件，如果不指定用户则删除当前用户的 crontab 文件内容
crontab -i # 删除用户的 crontab 文件时，给与确认提示
```

这里直接使用 ```crontab -e``` 编辑当前 root 用户的 crontab 文件

```
[root@Aprsun ~]# crontab -e
30 15 * * * python3 /usr/local/stock/sina_finance.py > /usr/local/stock/log.log 2>&1
# 每天15点30分 执行 sina_finance 文件 并重定向日志到 log.log
```

命令语法如下：

```
# Example of job definition:
# .---------------- minute (0 - 59)
# |  .------------- hour (0 - 23)
# |  |  .---------- day of month (1 - 31)
# |  |  |  .------- month (1 - 12) OR jan,feb,mar,apr ...
# |  |  |  |  .---- day of week (0 - 6) (Sunday=0 or 7) OR sun,mon,tue,wed,thu,fri,sat
# |  |  |  |  |
# *  *  *  *  * user-name  command to be executed

# Special characters:
# * (星号) 代表任何时间，"* * * * *" 代表每分钟执行一次命令
# , (逗号) 代表不连续的时间，"15 1,3,5 * * *" 代表每天的1点15分，3点15分，5点15分都执行一次命令
# - (中杠) 代表连续的时间范围，"15 1 1-5 * *" 代表每个月的1号到5号的1点15分执行命令
# / (正斜线) 代表每个多久执行一次，"*/10 4 * * *" 代表在每天的4点，每隔10分钟执行一次命令 
```

运行 restart 命令，重启服务，使定时任务生效

```service crond restart```

#### *注：

* 在 crond 命令中需要使用绝对路径写到命令，否则运行会失败
* 执行过程中，也可以通过 ```tail -f /var/log/cron```  命令，查看 crontab 的执行情况
* 代码中需要读写文件时，文件路径也需要修改成绝对路径，否则文件会保存到根目录下