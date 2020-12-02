# FTP_Server
根据老男孩博客作业：开发一个支持多用户在线的FTP程序

要求：
 1.用户加密认证（未完成）
 2.允许同时多用户登录
 3.每个用户有自己的家目录，且只能访问自己的家目录
 4.对用户今夕磁盘配额，每个用户的可用空间不同
 5.允许用户在ftp server上随意切换目录
 6.允许用户查看当前目录下文件。
 7.允许上传和下载文件，保证文件一致性。
 8.文件传输过程中显示进度条
 9.附加功能：支持文件的断点续传（未完成）
 
运行方式：(python3环境下)
FTP_server  启动
在  FTP_server/bin 目录下  执行  python  ftp_server.py start

FTP_client 启动
在  FTP_client/ 目录下  执行   python  ftp_client.py  -s 127.0.0.1(server在本地)  -P 9999  -u alex  -p 12345

备注：由于用户信息是写入配置文件中的，所以在启动前需要更改配置文件user_info.cfg，主要修改家目录

在 FTP_server/data/accounts/目录下  修改user_info.cfg  文件

[alex]
Password = 12345
Homedir = (FTP_server所在目录)/FTP_serever/home/alex
Quotation = 20
