#coding=UTF-8
# Licensed under the GPLv3
# 本项目由@Everyb0dyLies开发维护，使用python2.7
# 目前为测试版，win7, ubuntu1604测试通过，如有任何问题欢迎在本项目的github页面提交issue，或联系qq1768154526

import uuid, time, threading, struct, random, hashlib, re
import socket
import inspect, ctypes

# local config
USER_NAME = ""
PASSWORD = ""
LOCAL_MAC = ""
# login config
SERVER_IP = '192.168.211.3'
DHCP_SERVER_IP = '211.68.32.204'
CONTROL_CHECK_STATUS = '\x20'
ADAPTER_NUMBER = '\x01'
IP_DOG = '\x01'
AUTH_VERSION = '\x0a\x00'
KEEP_ALIVE_VERSION = '\x0f\x27'
# app config
RETRY_TIMES = 3


def _async_raise(tid, exctype):
    # 本函数参考 https://www.oschina.net/question/172446_2159505
    """raises the exception, performs cleanup if needed"""
    tid = ctypes.c_long(tid)
    if not inspect.isclass(exctype):
        exctype = type(exctype)
    res = ctypes.pythonapi.PyThreadState_SetAsyncExc(tid, ctypes.py_object(exctype))
    if res == 0:
        raise ValueError("invalid thread id")
    elif res != 1:
        # """if it returns a number greater than one, you're in trouble,
        # and you should call it again with exc=NULL to revert the effect"""
        ctypes.pythonapi.PyThreadState_SetAsyncExc(tid, None)
        raise SystemError("PyThreadState_SetAsyncExc failed")


def stop_thread(thread):
    # 本函数参考 https://www.oschina.net/question/172446_2159505
    _async_raise(thread.ident, SystemExit)


def log(log_type, err_no, msg):
    if log_type < LOG_MODE:
        return
    if log_type == 0:
        print "[info]" + msg
    if log_type == 1:
        print "[warning]" + msg
    if log_type == 2:
        print "[error]" + "err_no:" + str(err_no) + ", " + msg


def md5(str):
    m = m = hashlib.md5()
    m.update(str)
    return m.digest()


def int2hex_str(num):
    s = '%x' % num
    if len(s) & 1:
        s = '0' + s
    return s.decode('hex')


def checksum(s):
    ret = 1234
    for i in re.findall('....', s):
        ret ^= int(i[::-1].encode('hex'), 16)
    ret = (1968 * ret) & 0xffffffff
    return struct.pack('<I', ret)


def clean_socket_buffer(s):
    timeout = s.gettimeout()
    s.settimeout(0.01)
    while True:
        try:
            s.recvfrom(1024)
        except socket.timeout:
            break
    s.settimeout(timeout)


def print_bytes(bytes):
    #
    print "========================================================================"
    print "-NO-  00 01 02 03 04 05 06 07  08 09 0a 0b 0c 0d 0e 0f  --UTF_8-String--"
    for i in xrange(0, len(bytes), 16):
        print "%04x " % i,
        for j in xrange(i, i+16):
            if j < len(bytes):
                print bytes[j].encode('hex'),
            else:
                print "  ",
            if (j+1) % 8 == 0:
                print "",
        print bytes[i:i+16].decode('UTF-8', 'replace').replace('\n', '^')
    print "========================================================================"


class TimeoutException(Exception):
    def __init__(self):
        self.error_info = ""
        self.last_pkg = None


class Drcom(object):
    def __init__(self, usr=USER_NAME, pwd=PASSWORD):
        self.usr = usr
        self.pwd = pwd

        self.server_ip = ""
        self.salt = ""
        self.auth_info = ""

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        self.socket.settimeout(3)
        try:
            self.socket.bind(("", 61440))
        except socket.error as e:
            log(2, 11, "Can not bind the port 61440，please check your internet！")
            return None

    def prepare(self):
        # 获取服务器IP和Salt
        random_value = struct.pack("<H", int(time.time() + random.randint(0xF, 0xFF)) % (0xFFFF))
        pkg = '\x01\x02' + random_value + '\x0a' + '\x00' * 15

        if (not SERVER_IP == ''):
            last_times = RETRY_TIMES
            while last_times > 0:
                last_times = last_times - 1

                log(0, 0, "[prepare]：Trying to verify the Server IP and get the Salt...")
                clean_socket_buffer(self.socket)
                self.socket.sendto(pkg, (SERVER_IP, 61440))
                try:
                    data, address = self.socket.recvfrom(1024)
                except socket.timeout as e:
                    log(1, 0, "[prepare]：Timeout, retrying...")
                    continue

                if (data[0:4] == '\x02\x02' + random_value):
                    self.server_ip = address[0]
                    self.salt = data[4:8]
                    return True

                log(2, 20, "[prepare]：Receive unknown packages.")

        last_times = RETRY_TIMES
        while last_times > 0:
            last_times = last_times - 1

            log(0, 0, "[prepare]：Trying to get the Server IP and Salt...")
            clean_socket_buffer(self.socket)
            self.socket.sendto(pkg, ("1.1.1.1", 61440))
            self.socket.sendto(pkg, ("202.1.1.1", 61440))
            try:
                data, address = self.socket.recvfrom(1024)
            except socket.timeout as e:
                log(1, 0, "[prepare]：Timeout, retrying...")
                continue

            if (data[0:4] == '\x02\x02' + random_value):
                self.server_ip = address[0]
                self.salt = data[4:8]
                log(0, 0, "[prepare]：Server IP: " + self.server_ip)
                return True

            log(2, 21, "[prepare]：Receive unknown packages.")
        e = TimeoutException()
        e.error_info = "Can not get the Server IP and Salt！"
        e.last_pkg = pkg
        raise e

    def make_login_package(self):
        # 构造登陆包
        if (LOCAL_MAC == ""):  # 如果没有指定本机MAC，尝试自动获取
            local_mac = uuid.UUID(int=uuid.getnode()).hex[-12:].decode("hex")
        else:
            local_mac = LOCAL_MAC.decode("hex")
        local_host_name = socket.getfqdn(socket.gethostname())
        local_ip = socket.gethostbyname(local_host_name)

        data = '\x03\x01\x00' + chr(len(self.usr) + 20)  # (0:3 4) Header = Code + Type + EOF + (UserName Length + 20)
        data += md5('\x03\x01' + self.salt + self.pwd)  # (4:19 16) MD5_A = MD5(Code + Type + Salt + Password)
        data += self.usr.ljust(36, '\x00')  # (20:55 36) 用户名
        data += CONTROL_CHECK_STATUS  # (56:56 1) 控制检查状态
        data += ADAPTER_NUMBER  # (57:57 1) 适配器编号？
        data += int2hex_str(long(data[4:10].encode('hex'), 16) ^ long(local_mac.encode('hex'), 16)).rjust(6, '\x00')  # (58:63 6) (MD5_A xor MAC)
        data += md5('\x01' + self.pwd + self.salt + '\x00'*4)  # (64:79 16) MD5_B = MD5(0x01 + Password + Salt + 0x00 *4)
        data += '\x01'  # (80:80 1) NIC Count
        data += socket.inet_aton(local_ip)  # (81:84 4) 本机IP
        data += '\00' * 4  # (85:88 4) ip地址 2
        data += '\00' * 4  # (89:92 4) ip地址 3
        data += '\00' * 4  # (93:96 4) ip地址 4
        data += md5(data + '\x14\x00\x07\x0b')[:8]  # (97:104 8) 校验和A
        data += IP_DOG  # (105:105 1) IP Dog
        data += '\x00' * 4  # (106:109 4) 未知
        data += local_host_name.ljust(32, '\x00')  # (110:141 32) 主机名
        data += '\x72\x72\x72\x72'  # (142:145 4) 主要dns: 114.114.114.114
        data += socket.inet_aton(DHCP_SERVER_IP)  # (146:149 4) DHCP服务器IP
        data += '\x08\x08\x08\x08'  # (150:153 4) 备用dns:8.8.8.8
        data += '\x00' * 8  # (154:161 8) 未知
        data += '\x94\x00\x00\x00'  # (162:165 4) 未知
        data += '\x06\x00\x00\x00'  # (166:169 4) OS major 不同客户端有差异
        data += '\x01\x00\x00\x00'  # (170:173 4) OS minor 不同客户端有差异
        data += '\xb1\x1d\x00\x00'  # (174:177 4) OS build 不同客户端有差异
        data += '\x02\x00\x00\x00'  # (178:181 4) 未知 OS相关
        data += "WINDOWS".ljust(32, '\x00')  # (182:213 32) 操作系统名称
        data += '\x00' * 96  # (214:309 96) 未知 不同客户端有差异，BISTU版此字段包含一段识别符，但不影响登陆
        data += AUTH_VERSION  # (310:311 2)
        data += '\x02\x0c'  # (312:313 2) 未知
        data += checksum(data + '\x01\x26\x07\x11\x00\x00' + local_mac)  # (314:317 4) 校验和
        data += '\x00\x00'  # (318:319 2) 未知
        data += local_mac   # (320:325 6) 本机MAC
        data += '\x00'  # (326:326 1) auto logout / default: False
        data += '\x00'  # (327:327 1) broadcast mode / default : False
        data += '\x17\x77'  # (328:329 2) 未知 不同客户端有差异
        return data

    def login(self):
        # 登陆
        pkg = self.make_login_package()

        last_times = RETRY_TIMES
        while last_times > 0:
            last_times = last_times - 1

            log(0, 0, "[login]：Sending the login request...")
            clean_socket_buffer(self.socket)
            self.socket.sendto(pkg, (self.server_ip, 61440))
            try:
                data, address = self.socket.recvfrom(1024)
            except socket.timeout as e:
                log(1, 0, "[login]：Timeout, retrying...")
                continue

            if (data[0] == '\x04'):
                self.auth_info = data[23:39]
                log(0, 0, "[login]：Login success.")
                return True
            if (data[0] == '\x05'):
                if (data[32] == '\x31'):
                    log(2, 31, "Wrong username！")
                if (data[32] == '\x33'):
                    log(2, 32, "Wrong password！")
                return False

            log(2, 30, "[login]：Receive unknown packages.")
        e = TimeoutException()
        e.error_info = "Can not login！"
        e.last_pkg = pkg
        raise e

    def send_alive_pkg1(self):
        # 发送心跳包
        pkg = '\xff'
        pkg += md5('\x03\x01' + self.salt + self.pwd)  # MD5_A
        pkg += '\x00' * 3  # 未知
        pkg += self.auth_info
        pkg += struct.pack('!H', int(time.time()) % 0xFFFF)
        # pkg += '\x00' * 3

        last_times = RETRY_TIMES
        while last_times > 0:
            last_times = last_times - 1

            log(0, 0, "[send_alive_pkg1]：Sending alive pkg1...")
            clean_socket_buffer(self.socket)
            self.socket.sendto(pkg, (self.server_ip, 61440))
            try:
                data, address = self.socket.recvfrom(1024)
            except socket.timeout as e:
                log(1, 0, "[send_alive_pkg1]：Timeout, retrying...")
                continue

            if (data[0] == '\x07'):
                log(0, 0, "[send_alive_pkg1]：Alive pkg1 send success")
                return True

            log(2, 40, "[send_alive_pkg1]：Receive unknown packages.")
        e = TimeoutException()
        e.error_info = "Alive pkg1 send failed！"
        e.last_pkg = pkg
        raise e

    def make_alive_package(self, num, key, type):
        # 构造心跳包
        data = '\x07'  # (0:0 1) 未知
        data += chr(num)  # (1:1 1) 编号
        data += '\x28\x00\x0b'  # (2:4 3) 未知
        data += chr(type)  # (5:5 1) 类型
        if (num == 0):  # (6:7 2) BISTU版此字段不会变化
            data += '\x0f\x27'
        else:
            data += KEEP_ALIVE_VERSION
        data += '\x2f\x12'  # (8:9 2) 未知 每个包会有变化
        data += '\x00' * 6  # (10:15 6) 未知
        data += key  # (16:19 4)
        data += '\x00' * 4  # (20:23 4) 未知
        # data += struct.pack("!H",0xdc02)  # 未验证

        if (type == 1):
            data += '\x00' * 16  # (24:39 16) 未知
        if (type == 3):  # 未验证
            local_host_name = socket.getfqdn(socket.gethostname())
            local_ip = socket.gethostbyname(local_host_name)

            foo = ''.join([chr(int(i)) for i in local_ip.split('.')])  # host_ip
            # use double keep in main to keep online .Ice
            crc = '\x00' * 4
            # data += struct.pack("!I",crc) + foo + '\x00' * 8
            data += crc + foo + '\x00' * 8
        return data

    def send_alive_pkg2(self, num, key, type=3):
        # 发送心跳包
        pkg = self.make_alive_package(num = num, key = key, type = type)

        last_times = RETRY_TIMES
        while last_times > 0:
            last_times = last_times - 1

            log(0, 0, "[send_alive_pkg2]：Sending alive pkg2，NO：%d..." % num)
            clean_socket_buffer(self.socket)
            self.socket.sendto(pkg, (self.server_ip, 61440))
            try:
                data, address = self.socket.recvfrom(1024)
            except socket.timeout as e:
                log(1, 0, "[send_alive_pkg2]：Timeout, retrying...")
                continue

            if (data[0] == '\x07'):
                log(0, 0, "[send_alive_pkg2]：Alive pkg2 send success，NO：%d" % num)
                return data[16:20]

            log(2, 50, "[send_alive_pkg2]：Receive unknown packages.")
        e = TimeoutException()
        e.error_info = "Alive pkg2 send failed，NO:%d！" % num
        e.last_pkg = pkg
        raise e

    def keep_alive(self):
        num = 1
        key = '\x00' * 4
        while True:
            try:
                self.send_alive_pkg1()

                if (num == 0 or num == 1):
                    key = self.send_alive_pkg2(num, '\x00' * 4)

                else:
                    key = self.send_alive_pkg2(num, key)

            except TimeoutException as e:
                log(2, 60, "[keep_alive]：" + e.error_info)
                return False

            num = num + 1
            time.sleep(20)

    def make_logout_package(self):
        if (LOCAL_MAC == ""):  # 如果没有指定本机MAC，尝试自动获取
            local_mac = uuid.UUID(int=uuid.getnode()).hex[-12:].decode("hex")
        else:
            local_mac = LOCAL_MAC.decode("hex")

        data = '\x06\x01\x00' + chr(len(self.usr) + 20)  # (0:3 4) Header = Code + Type + EOF + (UserName Length + 20)
        # TODO MD5_A字段在BISTU版中的算法未知，但以下算法可以正常使用
        data += md5('\x06\x01' + self.salt + self.pwd)  # (4:19 16) MD5_A = MD5(Code + Type + Salt + Password)
        data += self.usr.ljust(36, '\x00')  # (20:55 36) 用户名
        data += CONTROL_CHECK_STATUS  # (56:56 1) 控制检查状态
        data += ADAPTER_NUMBER  # (57:57 1) 适配器编号？
        data += int2hex_str(long(data[4:10].encode('hex'), 16) ^ long(local_mac.encode('hex'), 16)).rjust(6, '\x00')  # (58:63 6) (MD5_A xor MAC)
        data += self.auth_info
        return data

    def logout(self):
        '''
        登出，仅测试了BISTU版本
        登出过程一共会有6个包，分3组，每组2个
        第一组同alive_pkg1的发送与确认
        第二组似乎是用于告知网关准备登出
        第三组会发送登出的详细信息包括用户名等
        '''
        # 第一组
        self.send_alive_pkg1()  # 发送的数据包的最后两个字节可能有验证功能

        # 第二组 登出准备
        pkg = '\x01\x03'
        pkg += '\x00\x00'  # 与alive_pkg1的最后两个字节相同
        pkg += '\x0a'
        pkg += '\x00' * 15

        last_times = RETRY_TIMES
        while last_times > 0:
            last_times = last_times - 1

            log(0, 0, "[logout]：Sending logout prepare pkg...")
            clean_socket_buffer(self.socket)
            self.socket.sendto(pkg, (self.server_ip, 61440))
            try:
                data, address = self.socket.recvfrom(1024)
            except socket.timeout as e:
                log(1, 0, "[logout]：Timeout, retrying...")
                continue

            if (data[0:2] == '\x02\x03'):
                log(0, 0, "[logout]：Logout prepare pkg send success.")
                break

            log(2, 70, "[logout]：Receive unknown packages.")
        if (last_times == 0):
            e = TimeoutException()
            e.error_info = "Logout prepare pkg send failed！"
            e.last_pkg = pkg
            raise e

        # 第三组
        pkg = self.make_logout_package()

        last_times = RETRY_TIMES
        while last_times > 0:
            last_times = last_times - 1

            log(0, 0, "[logout]：Sending the logout request...")
            clean_socket_buffer(self.socket)
            self.socket.sendto(pkg, (self.server_ip, 61440))
            try:
                data, address = self.socket.recvfrom(1024)
            except socket.timeout as e:
                log(1, 0, "[logout]：Timeout, retrying...")
                continue

            if (data[0] == '\x04'):
                log(0, 0, "[logout]：Logout success.")
                return True

            log(2, 71, "[logout]：Receive unknown packages.")
            print_bytes(data)
        e = TimeoutException()
        e.error_info = "Logout failed！"
        e.last_pkg = pkg
        raise e


if __name__ == "__main__":
    print "欢迎使用专为北信科开发的liarcom"
    print "本项目由@Everyb0dyLies开发维护"
    print "目前为测试版，如有任何问题欢迎在本项目的github页面提交issue"
    drcom = Drcom()

    try:
        if (not drcom.prepare()):
            exit()
        if (not drcom.login()):
            exit()
        keep_alive_thread = threading.Thread(target = drcom.keep_alive, args =())
        keep_alive_thread.start()

        print "登陆成功，登出请输入logout。"
        while True:
            user_input = raw_input()
            if (user_input == "logout"):
                stop_thread(keep_alive_thread)
                drcom.logout()
                break
            else:
                print "登出请输入logout。"
    except TimeoutException as e:
        log(2, 10, "[main]：" + e.error_info)

