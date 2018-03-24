# -*- coding: utf-8 -*-
# Licensed under the GPLv3
# 本项目由@Everyb0dyLies开发维护，使用python3

from tools import *
import uuid, time, random, struct, socket, threading, sys, logging

# local config
USER_NAME = ""
PASSWORD = ""
LOCAL_MAC = ""  # 选填，默认为空，应填写本机网卡MAC，全小写，无连接符，如：001a264a7b0d
LOCAL_IP = ""  # 选填，默认为空，应填写本机IP，如：192.168.100.123
# app config
AUTO_RELOGIN = True
RETRY_TIMES = 3
LOG_LEVEL = logging.INFO
# login config  # 请勿随意更改
SERVER_IP = '192.168.211.3'
DHCP_SERVER_IP = '211.68.32.204'
CONTROL_CHECK_STATUS = b'\x20'
ADAPTER_NUMBER = b'\x01'
IP_DOG = b'\x01'
AUTH_VERSION = b'\x0a\x00'
KEEP_ALIVE_VERSION = b'\xdc\x02'


class Liarcom(object):
    def __init__(self, usr=USER_NAME, pwd=PASSWORD):
        print("欢迎使用专为北信科开发的liarcom")
        print("本项目由@Everyb0dyLies开发维护")
        print("目前为测试版，如有任何问题欢迎在本项目的github页面提交issue")

        self._usr = usr
        self._pwd = pwd
        self._drcom = Drcom(self._usr, self._pwd)
        self._auto_relogin_flag = AUTO_RELOGIN
        self._relogin_timeout = 300
        self._relogin_retry_times = RETRY_TIMES

    @property
    def user(self):
        return self._usr

    @user.setter
    def user(self, value):
        if (value == ""):
            raise LiarcomException("用户名错误！")
        self._usr = value
        self._drcom.usr = value

    @property
    def password(self):
        return self._pwd

    @password.setter
    def password(self, value):
        if (value == ""):
            raise LiarcomException("密码错误！")
        self._pwd = value
        self._drcom.pwd = value

    @property
    def auto_relogin_flag(self):
        return self._auto_relogin_flag

    @auto_relogin_flag.setter
    def auto_relogin_flag(self, value):
        self._auto_relogin_flag = value

    @property
    def relogin_retry_times(self):
        return self._relogin_retry_times

    @relogin_retry_times.setter
    def relogin_retry_times(self, value):
        self._relogin_retry_times = value

    @property
    def relogin_timeout(self):
        return self._relogin_timeout

    @relogin_timeout.setter
    def relogin_timeout(self, value):
        self._relogin_timeout = value

    @property
    def status(self):
        if self._drcom.login_flag:
            if self._drcom.keep_alive_flag:
                return "online"
            else:
                return "timeout"
        else:
            return "offline"

    def login(self):
        self._login()
        if self.auto_relogin_flag:
            auto_relogin_thread = threading.Thread(target = self._auto_relogin, args =())
            auto_relogin_thread.start()
            Log(logging.INFO, 0, "[Liarcom.login]：已启动自动重登陆线程。")

    def _login(self):
        if (self._drcom.usr == "" or self._drcom.pwd == ""):
            raise LiarcomException("缺少必要参数！")
        Log(logging.INFO, 0, "[Liarcom._login]：开始登陆。")
        try:
            if (not self._drcom.prepare()):
                Log(logging.ERROR, 111, "[Liarcom._login]：登陆失败！")
                return
            if (not self._drcom.login()):
                Log(logging.ERROR, 112, "[Liarcom._login]：登陆失败！")
                return
            keep_alive_thread = threading.Thread(target = self._drcom.keep_alive, args =())
            keep_alive_thread.start()
            Log(logging.INFO, 0, "[Liarcom._login]：登陆成功，已启动心跳保持线程。")
        except DrcomException as e:
            Log(logging.ERROR, 110, "[Liarcom._login]：登陆失败，" + e.info)
            
    def _auto_relogin(self):
        time_flag = time.time() - self._relogin_timeout
        last_times = self._relogin_retry_times
        while (self.auto_relogin_flag and self._drcom.login_flag):
            if (self.status == "timeout"):
                if (last_times <= 0):
                    Log(logging.ERROR, 120, "[Liarcom._auto_relogin]：超出最大重试次数！")
                    self._drcom.login_flag = False
                    raise LiarcomException("[Liarcom]已在%ds内重试登录%d次，但没有成功！" % (self._relogin_timeout, self._relogin_retry_times))
                if (last_times == self._relogin_retry_times):
                    time_flag = time.time()
                last_times = last_times - 1
                Log(logging.WARNING, 0, "[Liarcom._auto_relogin]：开始重新登录，剩余%d次。" % last_times)
                self._login()
            else:
                if (not last_times == self._relogin_retry_times and time.time() - time_flag > self._relogin_timeout):
                    Log(logging.INFO, 0, "[Liarcom._auto_relogin]：重设重试次数。")
                    last_times = self._relogin_retry_times
                time.sleep(0.1)

    def logout(self):
        if (self._drcom.usr == "" or self._drcom.pwd == ""):
            raise LiarcomException("缺少必要参数！")
        if (self.status == "offline"):
            return
        
        Log(logging.INFO, 0, "[Liarcom.logout]：开始登出。")
        try:
            if (not self._drcom.logout()):
                Log(logging.ERROR, 131, "[Liarcom.logout]：登出失败！")
                return
            Log(logging.INFO, 0, "[Liarcom.logout]：登出成功。")
        except DrcomException as e:
            Log(logging.ERROR, 130, "[Liarcom.logout]：" + e.info)


class Drcom(object):
    def __init__(self, usr, pwd):
        self.usr = usr
        self.pwd = pwd

        self.server_ip = ""
        self.salt = b""
        self.auth_info = b""

        self.login_flag = False
        self.keep_alive_flag = False

        if (LOCAL_MAC == ""):  # 如果没有指定本机MAC，尝试自动获取
            self.mac = bytes().fromhex(uuid.UUID(int=uuid.getnode()).hex[-12:])
        else:
            self.mac = bytes().fromhex(LOCAL_MAC)
        self.host_name = socket.getfqdn(socket.gethostname())
        if (LOCAL_IP == ""):
            self.ip = socket.gethostbyname(self.host_name)
        else:
            self.ip = LOCAL_IP

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        self.socket.settimeout(3)
        try:
            self.socket.bind(("", 61440))
        except socket.error as e:
            Log(logging.ERROR, 10, "[Drcom.__init__]：无法绑定61440端口，请检查您的网络！")
            return None

    def prepare(self):
        # 获取服务器IP和Salt
        random_value = struct.pack("<H", int(time.time() + random.randint(0xF, 0xFF)) % (0xFFFF))
        pkg = b'\x01\x02' + random_value + b'\x0a' + b'\x00' * 15

        if (not SERVER_IP == ''):
            last_times = RETRY_TIMES
            while last_times > 0:
                last_times = last_times - 1

                Log(logging.INFO, 0, "[Drcom.prepare]：Trying to verify the Server IP and get the Salt...")
                clean_socket_buffer(self.socket)
                self.socket.sendto(pkg, (SERVER_IP, 61440))
                try:
                    data, address = self.socket.recvfrom(1024)
                except socket.timeout as e:
                    Log(logging.WARNING, 0, "[Drcom.prepare]：超时，重试中...")
                    continue

                if (data[0:4] == b'\x02\x02' + random_value):
                    self.server_ip = address[0]
                    self.salt = data[4:8]
                    return True

                Log(logging.ERROR, 20, "[Drcom.prepare]：Receive unknown packages.")

        last_times = RETRY_TIMES
        while last_times > 0:
            last_times = last_times - 1

            Log(logging.INFO, 0, "[Drcom.prepare]：Trying to get the Server IP and Salt...")
            clean_socket_buffer(self.socket)
            self.socket.sendto(pkg, ("1.1.1.1", 61440))
            self.socket.sendto(pkg, ("202.1.1.1", 61440))
            try:
                data, address = self.socket.recvfrom(1024)
            except socket.timeout as e:
                Log(logging.WARNING, 0, "[Drcom.prepare]：超时，重试中...")
                continue

            if (data[0:4] == b'\x02\x02' + random_value):
                self.server_ip = address[0]
                self.salt = data[4:8]
                Log(logging.INFO, 0, "[Drcom.prepare]：服务器IP: " + self.server_ip)
                return True

            Log(logging.ERROR, 21, "[Drcom.prepare]：Receive unknown packages.")
        e = TimeoutException("无法获取服务器IP和Salt！")
        e.last_pkg = pkg
        raise e

    def _make_login_package(self):
        # 构造登陆包
        data = b'\x03\x01\x00' + int2hex_str(len(self.usr) + 20)  # (0:3 4) Header = Code + Type + EOF + (UserName Length + 20)
        data += md5(b'\x03\x01' + self.salt + self.pwd.encode('ascii'))  # (4:19 16) MD5_A = MD5(Code + Type + Salt + Password)
        data += self.usr.encode('ascii').ljust(36, b'\x00')  # (20:55 36) 用户名
        data += CONTROL_CHECK_STATUS  # (56:56 1) 控制检查状态
        data += ADAPTER_NUMBER  # (57:57 1) 适配器编号？
        data += int2hex_str(int.from_bytes(data[4:10], 'big') ^ int.from_bytes(self.mac, 'big')).rjust(6, b'\x00')  # (58:63 6) (MD5_A xor MAC)
        data += md5(b'\x01' + self.pwd.encode('ascii') + self.salt + b'\x00'*4)  # (64:79 16) MD5_B = MD5(0x01 + Password + Salt + 0x00 *4)
        data += b'\x01'  # (80:80 1) NIC Count
        data += socket.inet_aton(self.ip)  # (81:84 4) 本机IP
        data += b'\00' * 4  # (85:88 4) ip地址 2
        data += b'\00' * 4  # (89:92 4) ip地址 3
        data += b'\00' * 4  # (93:96 4) ip地址 4
        data += md5(data + b'\x14\x00\x07\x0b')[:8]  # (97:104 8) 校验和A
        data += IP_DOG  # (105:105 1) IP Dog
        data += b'\x00' * 4  # (106:109 4) 未知
        data += self.host_name.encode('ascii').ljust(32, b'\x00')  # (110:141 32) 主机名
        data += b'\x72\x72\x72\x72'  # (142:145 4) 主要dns: 114.114.114.114
        data += socket.inet_aton(DHCP_SERVER_IP)  # (146:149 4) DHCP服务器IP
        data += b'\x08\x08\x08\x08'  # (150:153 4) 备用dns:8.8.8.8
        data += b'\x00' * 8  # (154:161 8) 未知
        data += b'\x94\x00\x00\x00'  # (162:165 4) 未知
        data += b'\x06\x00\x00\x00'  # (166:169 4) OS major 不同客户端有差异
        data += b'\x01\x00\x00\x00'  # (170:173 4) OS minor 不同客户端有差异
        data += b'\xb1\x1d\x00\x00'  # (174:177 4) OS build 不同客户端有差异
        data += b'\x02\x00\x00\x00'  # (178:181 4) 未知 OS相关
        data += "WINDOWS".encode('ascii').ljust(32, b'\x00')  # (182:213 32) 操作系统名称
        data += b'\x00' * 96  # (214:309 96) 未知 不同客户端有差异，BISTU版此字段包含一段识别符，但不影响登陆
        data += AUTH_VERSION  # (310:311 2)
        data += b'\x02\x0c'  # (312:313 2) 未知
        data += checksum(data + b'\x01\x26\x07\x11\x00\x00' + self.mac)  # (314:317 4) 校验和
        data += b'\x00\x00'  # (318:319 2) 未知
        data += self.mac   # (320:325 6) 本机MAC
        data += b'\x00'  # (326:326 1) auto logout / default: False
        data += b'\x00'  # (327:327 1) broadcast mode / default : False
        data += b'\x17\x77'  # (328:329 2) 未知 不同客户端有差异
        return data

    def login(self):
        # 登陆
        pkg = self._make_login_package()

        last_times = RETRY_TIMES
        while last_times > 0:
            last_times = last_times - 1

            Log(logging.INFO, 0, "[Drcom.login]：发送登陆请求...")
            clean_socket_buffer(self.socket)
            self.socket.sendto(pkg, (self.server_ip, 61440))
            try:
                data, address = self.socket.recvfrom(1024)
            except socket.timeout as e:
                Log(logging.WARNING, 0, "[Drcom.login]：超时，重试中...")
                continue
                
            if (data[0] == 0x04):
                self.auth_info = data[23:39]
                self.login_flag = True
                Log(logging.INFO, 0, "[Drcom.login]：登陆成功")
                return True
            if (data[0] == 0x05):
                if (data[32] == 0x31):
                    Log(logging.ERROR, 31, "学号错误！")
                if (data[32] == 0x33):
                    Log(logging.ERROR, 32, "密码错误！")
                return False
            
            Log(logging.ERROR, 30, "[Drcom.login]：Receive unknown packages.")
        e = TimeoutException("登陆失败！")
        e.last_pkg = pkg
        raise e

    def _send_alive_pkg1(self):
        # 发送心跳包
        pkg = b'\xff'
        pkg += md5(b'\x03\x01' + self.salt + self.pwd.encode('ascii'))  # MD5_A
        pkg += b'\x00' * 3  # 未知
        pkg += self.auth_info
        pkg += struct.pack('!H', int(time.time()) % 0xFFFF)
        # pkg += b'\x00' * 3

        last_times = RETRY_TIMES
        while last_times > 0:
            last_times = last_times - 1

            Log(logging.INFO, 0, "[Drcom.send_alive_pkg1]：发送心跳包pkg1...")
            clean_socket_buffer(self.socket)
            self.socket.sendto(pkg, (self.server_ip, 61440))
            try:
                data, address = self.socket.recvfrom(1024)
            except socket.timeout as e:
                Log(logging.WARNING, 0, "[Drcom.send_alive_pkg1]：超时，重试中...")
                continue

            if (data[0] == 0x07):
                Log(logging.INFO, 0, "[Drcom.send_alive_pkg1]：心跳包pkg1发送成功")
                return True

            Log(logging.ERROR, 40, "[Drcom.send_alive_pkg1]：Receive unknown packages.")
        e = TimeoutException("心跳包pkg1发送失败！")
        e.last_pkg = pkg
        raise e

    def _make_alive_package(self, num, key, type):
        # 构造心跳包
        data = b'\x07'  # (0:0 1) 未知
        data += int2hex_str(num % 256)  # (1:1 1) 编号
        data += b'\x28\x00\x0b'  # (2:4 3) 未知
        data += int2hex_str(type)  # (5:5 1) 类型
        if (num == 0):  # (6:7 2) BISTU版此字段不会变化
            data += b'\xdc\x02'
        else:
            data += KEEP_ALIVE_VERSION
        data += b'\x2f\x79'  # (8:9 2) 未知 每个包会有变化
        data += b'\x00' * 6  # (10:15 6) 未知
        data += key  # (16:19 4)
        data += b'\x00' * 4  # (20:23 4) 未知
        # data += struct.pack("!H",0xdc02)  # 未验证

        if (type == 1):
            data += b'\x00' * 16  # (24:39 16) 未知
        if (type == 3):  # 未验证
            foo = b''.join([int2hex_str(int(i)) for i in self.ip.split('.')])  # host_ip
            # use double keep in main to keep online .Ice
            crc = b'\x00' * 4
            # data += struct.pack("!I",crc) + foo + b'\x00' * 8
            data += crc + foo + b'\x00' * 8
        return data

    def _send_alive_pkg2(self, num, key, type):
        # 发送心跳包
        pkg = self._make_alive_package(num = num, key = key, type = type)

        last_times = RETRY_TIMES
        while last_times > 0:
            last_times = last_times - 1

            Log(logging.INFO, 0, "[Drcom.send_alive_pkg2]：发送心跳包pkg2，NO：%d..." % num)
            clean_socket_buffer(self.socket)
            self.socket.sendto(pkg, (self.server_ip, 61440))
            try:
                data, address = self.socket.recvfrom(1024)
            except socket.timeout as e:
                Log(logging.WARNING, 0, "[Drcom.send_alive_pkg2]：超时，重试中...")
                continue

            if (data[0] == 0x07):
                Log(logging.INFO, 0, "[Drcom.send_alive_pkg2]：心跳包pkg2发送成功，NO：%d" % num)
                return data[16:20]

            Log(logging.ERROR, 50, "[Drcom.send_alive_pkg2]：Receive unknown packages.")
        e = TimeoutException("心跳包pkg2发送失败，NO:%d！" % num)
        e.last_pkg = pkg
        raise e

    def keep_alive(self):
        num = 0
        key = b'\x00' * 4
        time_flag = time.time()
        while self.login_flag:
            self.keep_alive_flag = True
            if (time.time() >= time_flag):
                try:
                    self._send_alive_pkg1()
                    key = self._send_alive_pkg2(num, key, type=1)
                    key = self._send_alive_pkg2(num, key, type=3)
                except TimeoutException as e:
                    self.keep_alive_flag = False
                    Log(logging.ERROR, 60, "[Drcom.keep_alive]：" + e.info)
                    return

                num = num + 2
                time_flag = time_flag + 20
            else:
                time.sleep(0.1)
        self.keep_alive_flag = False

    def _make_logout_package(self):
        data = b'\x06\x01\x00' + int2hex_str(len(self.usr) + 20)  # (0:3 4) Header = Code + Type + EOF + (UserName Length + 20)
        # TODO MD5_A字段在BISTU版中的算法未知，但以下算法可以正常使用
        data += md5(b'\x06\x01' + self.salt + self.pwd.encode('ascii'))  # (4:19 16) MD5_A = MD5(Code + Type + Salt + Password)
        data += self.usr.encode('ascii').ljust(36, b'\x00')  # (20:55 36) 用户名
        data += CONTROL_CHECK_STATUS  # (56:56 1) 控制检查状态
        data += ADAPTER_NUMBER  # (57:57 1) 适配器编号？
        data += int2hex_str(int.from_bytes(data[4:10], 'big') ^ int.from_bytes(self.mac, 'big')).rjust(6, b'\x00')  # (58:63 6) (MD5_A xor MAC)
        data += self.auth_info
        return data

    def logout(self):
        self.login_flag = False
        while self.keep_alive_flag:
            time.sleep(0.1)

        '''
        登出，仅测试了BISTU版本
        登出过程一共会有6个包，分3组，每组2个
        第一组同alive_pkg1的发送与确认
        第二组似乎是用于告知网关准备登出
        第三组会发送登出的详细信息包括用户名等
        '''
        # 第一组
        self._send_alive_pkg1()  # 发送的数据包的最后两个字节可能有验证功能

        # 第二组 登出准备
        pkg = b'\x01\x03'
        pkg += b'\x00\x00'  # 与alive_pkg1的最后两个字节相同
        pkg += b'\x0a'
        pkg += b'\x00' * 15

        last_times = RETRY_TIMES
        while last_times > 0:
            last_times = last_times - 1

            Log(logging.INFO, 0, "[Drcom.logout]：发送登出准备包...")
            clean_socket_buffer(self.socket)
            self.socket.sendto(pkg, (self.server_ip, 61440))
            try:
                data, address = self.socket.recvfrom(1024)
            except socket.timeout as e:
                Log(logging.WARNING, 0, "[Drcom.logout]：超时，重试中...")
                continue

            if (data[0:2] == b'\x02\x03'):
                Log(logging.INFO, 0, "[Drcom.logout]：登出准备包发送成功。")
                break

            Log(logging.ERROR, 70, "[Drcom.logout]：Receive unknown packages.")
        if (last_times == 0):
            e = TimeoutException("登出准备包发送失败！")
            e.last_pkg = pkg
            raise e

        # 第三组
        pkg = self._make_logout_package()

        last_times = RETRY_TIMES
        while last_times > 0:
            last_times = last_times - 1

            Log(logging.INFO, 0, "[Drcom.logout]：发送登出请求...")
            clean_socket_buffer(self.socket)
            self.socket.sendto(pkg, (self.server_ip, 61440))
            try:
                data, address = self.socket.recvfrom(1024)
            except socket.timeout as e:
                Log(logging.WARNING, 0, "[Drcom.logout]：超时，重试中...")
                continue

            if (data[0] == 0x04):
                Log(logging.INFO, 0, "[Drcom.logout]：登出成功。")
                return True

            Log(logging.ERROR, 71, "[Drcom.logout]：Receive unknown packages.")
        e = TimeoutException("登出失败！")
        e.last_pkg = pkg
        raise e


class Log(object):
    def __init__(self, level, err_no, msg):
        logging.basicConfig(stream=sys.stdout, level=logging.INFO, format='%(asctime)s - [%(levelname)s]: %(message)s')
        if (level < LOG_LEVEL):
            return
        if (level == logging.INFO):
            logging.info(msg)
        if (level == logging.WARNING):
            logging.warning(msg)
        if (level == logging.ERROR):
            logging.error("err_no:" + str(err_no) + ", " + msg)

