#!_*_coding:utf-8_*_
#__author__:"Alex Li"
import os
import sys
import logging
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


USER_HOME =os.path.join(BASE_DIR,'home')
LOG_DIR = os.path.join(BASE_DIR,'log')
LOG_LEVEL = "DEBUG"

ACCOUNT_FILE ="%s/data/accounts/user_info.cfg" % BASE_DIR

HOST="0.0.0.0"
PORT=9999