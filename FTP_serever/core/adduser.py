import os,sys
abs_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(abs_path)
from conf import settings
import hashlib
import  json
import configparser

print(abs_path)
class UsrerAdd(object):
    def __init__(self,*args,**kwargs):
        self.name = args[0]
        self.password = args[1]
        self.dumpuser()
    @classmethod
    def adduser(cls,name,password):
        cls(name,password)
    def dumpuser(self):
        password = self.password
        pas1 = hashlib.md5()
        pas1.update(password.encode("utf-8"))
        password_md5 = pas1.hexdigest()
        os.mkdir(settings.BASE_DIR+self.name)
        use_msg ={
            'Password':self.password,
            'Homedir':settings.BASE_DIR+self.name,
            'Quotation':100
        }
        conf = configparser.ConfigParser()

        if os.path.isfile(settings.ACCOUNT_FILE):
            conf.read(settings.ACCOUNT_FILE)
            conf[self.name] = use_msg
            with open(settings.ACCOUNT_FILE,"w") as f:
                conf.write(f)
        else:
            conf[self.name] = use_msg
            with open(settings.ACCOUNT_FILE,"w") as f:
                conf.write(f)


m1 = UsrerAdd.adduser("tom",'12345')



