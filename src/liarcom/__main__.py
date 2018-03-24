# -*- coding: utf-8 -*-
# Licensed under the GPLv3
# 本项目由@Everyb0dyLies开发维护，使用python3
# 目前为测试版，win7, ubuntu1604测试通过，如有任何问题欢迎在本项目的github页面提交issue，或联系qq1768154526

from liarcom import *
from tools import log, LiarcomException
import threading


if __name__ == "__main__":
    liarcom = Liarcom()

    try:
        liarcom.login()

        print("登陆成功，登出请输入logout。")
        while True:
            user_input = input()
            if (user_input == "logout"):
                liarcom.logout()
                break
            else:
                print("登出请输入logout。")
    except LiarcomException as e:
        log(2, 10, "[main]：" + e.info)

