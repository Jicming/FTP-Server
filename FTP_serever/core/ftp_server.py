#__author__:"jcm"
import os,sys,subprocess
from os.path import join, getsize
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)
from conf import settings
import socketserver
import  json
import os
import subprocess
import configparser
import re
from pathlib import Path

SYSTEM_OS = sys.platform

STATUS_CODE  = {
    200 : "Task finished",
    250 : "Invalid cmd format, e.g: {'action':'get','filename':'test.py','size':344}",
    251 : "Invalid cmd ",
    252 : "Invalid auth data",
    253 : "Wrong username or password",
    254 : "Passed authentication",
    255 : "Filename doesn't provided",
    256 : "File doesn't exist on server",
    257 : "ready to send file",
    258 : "md5 verification",
    259 : "path doesn't exist on server",
    260 : "path changed",
    261 : "Directory doesn't provided",
    262 : "",
    263 : "Error: Out of disk space"
}


def Diskquota_wrapper(func):
    '''
    磁盘配额装饰器，只要获取从客户端传来的文件大小加上用户家目录内文件的大小只要不大于配额就通过
    :param func:
    :return:
    '''
    def wrapper(*args, **kwargs):
        user = args[0].user.name
        home_dir = args[0].home_dir
        file_size = args[1]['size'] // 1024
        config = configparser.ConfigParser()  #读取配置文件 ，获取用户信息
        config.read(settings.ACCOUNT_FILE)
        home_size = 0
        for root, dirs, files in os.walk(home_dir):
            file_sums = sum([getsize(join(root, file)) for file in files]) // 1024
            home_size += file_sums
        total_size =home_size + file_size
        if total_size < int(config[user].get('Quotation'))*1024:  #将现有文件和配置文件中的配额进行对比
            res = func(*args,**kwargs)
            return res
        else:
            return args[0].send_response(263, data=STATUS_CODE[263])
    return wrapper





class MyFTPHandler(socketserver.BaseRequestHandler):
    """
    The request handler class for our server.

    Tt is instantiated once per connection to the server, and must
    override the handle() method to implement communication to the
    client.
    """

    def handle(self):
        #self.request is the TCP socket connected to the client
        while True:
            try:
                self.data = self.request.recv(1024).strip()
                print("{} wrote:".format(self.client_address[0]))
                cmd_dic = json.loads(self.data.decode())
                action = cmd_dic.get("action")
                if action is not None:

                    if action == "ls" or action == "dir":
                        action = "listdir"
                    if hasattr(self,"_%s"%action):
                        func = getattr(self,"_%s"%action)
                        func(cmd_dic)
                    else:
                        print("invalid cmd")
                        self.send_response(251)
                else:
                    print("invalid cmd format")
                    self.send_response(250)

            except ConnectionResetError  as e:
                print("client closed")
                break
            except json.decoder.JSONDecodeError as  e:
                print("client closed")
                break
    def send_response(self,status_code,data=None):
        response = {'status_code': status_code,
                    'status_msg': STATUS_CODE[status_code],
                    }
        if data:
            response.update({"data":data})
        self.request.send(json.dumps(response).encode())
    def _auth(self,*args,**kwargs):
        data = args[0]
        if data.get("username") is  None and data.get("password") is  None:
            self.send_response(252)
        user = self.authenticate(data.get("username"),data.get("password"))
        if user is None:
            self.send_response(253)
        else:
            print("passed authentication",user)
            self.user = user

            self.current_dir = (" ~ home/%s"%data.get("username"),Path(settings.USER_HOME)/data.get("username"))
            self.send_response(254,data=self.current_dir[0])

    def authenticate(self,username,password):
        config = configparser.ConfigParser()
        config.read(settings.ACCOUNT_FILE)
        if username in config.sections():
            _password = config[username]["Password"]
            if _password == password:
                config[username]["Username"]=username
                self.home_dir = Path(config[username]['Homedir'])
                return config[username]

    def _listdir(self,*arga,**kwargs):
        if SYSTEM_OS.startswith('win'):
            res = self.run_cmd("dir %s"%self.current_dir[1])
            return self.send_response(200,res)
        elif SYSTEM_OS.startswith("linux"):
            res = self.run_cmd("ls %s"%self.current_dir[1])
            return self.send_response(200,res)
    def run_cmd(self,cmd):
        cmd_res = subprocess.getstatusoutput(cmd)
        return  cmd_res

    def _cd(self,*args):
        '''
        切换目录，
        :param args: 客户端传来的命令信息
        :return: 无
        '''
        data = args[0]
        dirname = data.get('dirname')
        current_dir=''
        #判断是否有../../这样的目录名传进来
        cd_dir = re.findall('(\.{2}/)',dirname) if re.findall(r'^(\.{2}/)',dirname) else ''
        if dirname != '':
            if re.match('^[A-Z,a-z]+:',dirname):
                current_dir = dirname
            elif cd_dir:
                cd_len= len([i for i in cd_dir if i != ''])
                dirname = dirname.replace('../','') if dirname.replace('../','') != '..' and dirname.replace('../','') != '.' else ''
                if SYSTEM_OS.startswith('win'):
                    current_dir = Path('\\'.join(str(self.current_dir[1]).split('\\')[0:-cd_len]))/dirname
                elif SYSTEM_OS.startswith('linux'):
                    current_dir = Path('/'.join(str(self.current_dir[1]).split('/')[0:-cd_len])) / dirname
            elif re.findall('([\u4e00-\u9fa5\s\w])+$',dirname):
                current_dir = Path(self.current_dir[1])/dirname
            else:
                current_dir = self.current_dir[1]
            if str(current_dir).startswith(str(self.home_dir)):
                user_flog = str(self.user).split(':')[1].strip().strip('>')
                if os.path.isdir(current_dir):
                    self.current_dir =(" ~ home%s%s"%(user_flog,str(current_dir).split(user_flog)[1]),current_dir)
                    return  self.send_response(260,data={'current_dir':str(self.current_dir[0])})
                else:
                    return  self.send_response(259, data=STATUS_CODE[259])
            else:
                return  self.send_response(261,data=STATUS_CODE[261])
        else:
            return  self.send_response(262)
    def _pwd(self,*args):
        cmd_dir = args[0]
        self.send_response(200,data=str(self.current_dir[1]))

    @Diskquota_wrapper
    def _put(self,*args):

        '''
        接收客户端文件
        :return:
        '''

        cmd_dic = args[0]
        filename = cmd_dic["filename"]
        filesize = cmd_dic["size"]

        filepath = self.current_dir[1]/filename
        if os.path.isfile(filepath):
            f = open(str(filepath)+".new","wb")
        else:
            f = open(filepath,"wb")
        self.send_response(200,data=STATUS_CODE[200])
        # self.request.send(b"200 ok")
        received_size = 0
        while received_size <filesize:
            data = self.request.recv(1024)
            f.write(data)
            received_size += len(data)
        else:
            print("file [%s] has uploaded.."%filename)
            f.close()
        return filesize
    def _get(self,*args):
        cmd_dic = args[0]
        filename = cmd_dic["filename"]
        filepath = self.current_dir[1]/filename
        if os.path.isfile(filepath):
            filesize = os.stat(filepath).st_size
            msg_dic = {
                "size": filesize,
                "overridden": True
            }
            self.send_response(200,data=msg_dic)
            # self.request.send(json.dumps(msg_dic).encode("utf-8"))
            client_response = self.request.recv(1024)
            f = open(filepath,"rb")
            for line in f:
                self.request.send(line)
                # self.request.send(json.dumps(line).encode("utf-8"))
        else:
            self.send_response(256,data=STATUS_CODE[256])
            # self.request.send(json.dumps("file is not Exist").encode("utf-8"))



