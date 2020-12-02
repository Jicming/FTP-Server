#__author__:"jcm"
import  optparse
import os,sys
BASE_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_PATH)
from  core import ftp_server
from conf import settings
import socketserver


class ArvgHandler(object):
    def __init__(self,filename=os.path.basename(__file__)):
        self.filename = filename
        self.parser = optparse.OptionParser()
        (options,args) = self.parser.parse_args()
        self.verify_args(options,args)
    def verify_args(self,options,args):
        if args:
            if hasattr(self,args[0]):
                func = getattr(self,args[0])
                func()
            else:
                exit("usage:python %s start/stop"%self.filename)
        else:
            exit("usage:python %s start/stop"%self.filename)
    def start(self):
        print('---\033[32;1mStarting FTP server on %s:%s\033[0m----' %(settings.HOST, settings.PORT))
        server = socketserver.ThreadingTCPServer((settings.HOST,settings.PORT),ftp_server.MyFTPHandler)

        server.serve_forever()