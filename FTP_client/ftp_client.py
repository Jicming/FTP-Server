import socket
import json
import os,time
import optparse

STATUS_CODE  = {
    250 : "Invalid cmd format, e.g: {'action':'get','filename':'test.py','size':344}",
    251 : "Invalid cmd ",
    252 : "Invalid auth data",
    253 : "Wrong username or password",
    254 : "Passed authentication",
    261 : "No files in the directory"
}

class FtpClient(object):
    def __init__(self):
        self.user=None
        self.current_path=None
        parse = optparse.OptionParser()
        parse.add_option("-s","--server",dest="server",help = "ftp server ip_addr")
        parse.add_option("-P","--port",dest="port",type=int,help="ftp server port")
        parse.add_option("-u","--username",dest="username",help="ftp server username")
        parse.add_option("-p","--password",dest="password",help="ftp server password")
        self.option,self.args = parse.parse_args()
        self.verify_args(self.option,self.args)

        self.percentage =''


        self.make_connection()

    def verify_args(self,options,args):
        if options.username is not None and options.password is not None:
            pass
        elif options.username is None and options.password is None:
            exit("用户名和密码不能为空")
        else:
            exit("用户名和密码需要同时提供")
        if options.server and options.port:
            if options.port>0 and options.port <65535:
                return True
            else:
                exit("端口必须在0~65535之间")
        else:
            exit("Error:必须提供 ftp 服务地址，使用%s -h 查看全部可用参数"%__file__)

    def make_connection(self):
        self.client = socket.socket()
        self.client.connect((self.option.server,self.option.port))
    def authenticate(self,flog=True):
        if flog:
            self.retry_count = -1
            return self.get_auth_result(self.option.username,self.option.password)
        else:
            self.retry_count +=1
            while self.retry_count <3:
                self.option.username = input("username: ").strip()
                self.option.password = input("password: ").strip()
                if self.get_auth_result(self.option.username,self.option.password):
                    return True
        exit()


    def get_auth_result(self,username,password):
        data = {
            "action":'auth',
            "username":username,
            "password":password
        }
        self.client.send(json.dumps(data).encode())
        response = self.get_response()
        if response.get("status_code") == 254:
            print("用户验证成功！")
            self.user = self.option.username
            self.current_path = response.get("data")
            return True
        else:
            print(response.get("status_msg"))
            return self.authenticate(flog=False)

    def get_response(self):
        response = self.client.recv(1024)
        data = json.loads(response.decode('utf-8'))
        return data
    def help(self):
        msg = '''
        ls 
        pwd
        cd ../..
        get filename
        put filename
        '''
        print(msg)
    def connect(self,ip,port):
        self.client = socket.socket()
        self.client.connect((ip,port))
    def interactive(self):
        if self.authenticate():
            print("---欢迎 %s 登录 ftp 服务器..."%self.user)
            self.terminal_display = "[%s@%s] "%(self.user,self.current_path)
        while True:
            choice = input(self.terminal_display).strip()
            if len(choice) ==0:continue
            cmd_str = choice.split()[0]
            if hasattr(self,"cmd_%s"%cmd_str):
                func = getattr(self,"cmd_%s"%cmd_str)
                func(choice)
            else:
                self.help()

    def cmd_ls(self,*args):
        '''

        :param args:
        :return:
        '''
        cmd_split = args[0].split()
        if len(cmd_split) >0:
            msg_dic={"action":"ls"}
            self.client.send(json.dumps(msg_dic).encode())
            server_responce = self.get_response()
            if type(server_responce) is dict:
                if server_responce.get('status_code') == 200:
                    data = server_responce.get("data")
                    if data:
                        print(data[1])
                else:
                    print("Error:something wrong.")

    def cmd_cd(self,*args):
        cmd_split = args[0].split()
        dirname = ''
        if len(cmd_split) >1:
            dirname = cmd_split[1]
        msg_dic = {
            "action":"cd",
            "dirname":dirname
        }
        self.client.send(json.dumps(msg_dic).encode())
        server_responce = self.get_response()
        if type(server_responce) is dict:
            if server_responce.get('status_code') == 260:
                data = server_responce.get("data")
                self.terminal_display = "[%s@%s] " % (self.user, data.get('current_dir'))
                # self.current_path = data.get('current_dir')
                # print(self.current_path)
            if server_responce.get('status_code') == 259:
                print(server_responce.get('data'))
            if server_responce.get("status_code") == 261:
                print(server_responce.get('data'))
    def cmd_pwd(self,*args):
        data = args[0]
        msg = {'action':data}
        self.client.send(json.dumps(msg).encode())

        recv_data = self.get_response()
        if recv_data['status_code'] ==200:
            print(recv_data['data'])

    def cmd_put(self, *args):
        cmd_split = args[0].split()
        if len(cmd_split) > 1:
            filename = cmd_split[1]
            if os.path.isfile(filename):
                filesize = os.stat(filename).st_size
                msg_dic = {
                    "action": "put",
                    "filename": filename,
                    "size": filesize,
                    "overridden": True
                }
                self.client.send(json.dumps(msg_dic).encode("utf-8"))
                # 防止粘包，等服务器确认
                server_response = self.get_response()

                if server_response['status_code'] == 200:
                    f = open(filename, "rb")
                    receicesieze = 0
                    for line in f:
                        self.client.send(line)
                        receicesieze += len(line)
                        self.progress_bar(receicesieze,filesize)
                    else:
                        print("file upload success...")
                        f.close()
                elif server_response['status_code'] == 263:
                    print(server_response['status_msg'])
            else:
                print(filename, "is not Exist")

    def cmd_get(self,*args):
        cmd_split = args[0].split()
        if len(cmd_split) >1:
            filename = cmd_split[1]
            msg_dic={
                "action":"get",
                "filename":filename
            }
            self.client.send(json.dumps(msg_dic).encode())
            server_response = self.get_response()
            if type(server_response.get('data')) is dict:
                filesize = server_response.get('data')['size']
                self.client.send(b"200 ok")
                receicesieze = 0
                if not os.path.isfile(filename):
                    f = open(filename, "wb")
                else:
                    f = open(filename+'new','wb')


                while receicesieze < filesize:
                    data = self.client.recv(1024)
                    datanow = float(receicesieze) /float(filesize)
                    f.write(data)
                    # pro_bar = int(float('%.2f'%datanow)*50)
                    # if float('%.2f'%(datanow*100)) % 1 == 0.0 and  '%.0f%%'%(datanow*100) != percentage:
                    #     print('['+'>'*pro_bar,'%.0f%%'%(datanow*100)+']')
                    #     percentage = '%.0f%%'%(datanow*100)
                    receicesieze += len(data)
                    self.progress_bar(receicesieze,filesize)
                else:
                    print("file get success...")
            else:
                print(server_response.get('data'))

    def progress_bar(self,*args):
        receicesieze= args[0]
        filesize = args[1]
        datanow = float(receicesieze) / float(filesize)
        pro_bar = int(float('%.2f' % datanow) * 50)
        if float('%.2f' % (datanow * 100)) % 1 == 0.0 and '%.0f%%' % (datanow * 100) != self.percentage:
            print( '%s Mb'%(receicesieze//1024//1024) , '[' + '>' * pro_bar, '%.0f%%' % (datanow * 100) + ' ]' ,end='\r')
            self.percentage = '%.0f%%' % (datanow * 100)
        elif receicesieze == filesize:
            print('')

try:
    ftp = FtpClient()

    ftp.interactive()

except KeyboardInterrupt as e:
    print('退出 ftp 服务器...')



















