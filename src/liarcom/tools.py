# -*- coding: utf-8 -*-

import hashlib, struct, socket

# app config
PRINT_MODE = 0
LOG_MODE = 0


class DrcomException(Exception):
    def __init__(self, *args, **kwargs):
        super(DrcomException, self).__init__(args, kwargs)
        if (len(args[0]) > 0):
            self.info = args[0][0]


class LiarcomException(Exception):
    def __init__(self, *args, **kwargs):
        super(LiarcomException, self).__init__(args, kwargs)
        if (len(args[0]) > 0):
            self.info = args[0][0]


class TimeoutException(DrcomException):
    def __init__(self, *args, **kwargs):
        super(TimeoutException, self).__init__(args, kwargs)
        self.last_pkg = None


def log(log_type, err_no, msg):
    if (log_type < PRINT_MODE):
        return
    if (log_type == 0):
        print("[info]" + msg)
    if (log_type == 1):
        print("[warning]" + msg)
    if (log_type == 2):
        print("[error]" + "err_no:" + str(err_no) + ", " + msg)


def md5(str):
    m = hashlib.md5()
    m.update(str)
    return m.digest()


def int2hex_str(num):
    s = '%x' % num
    if len(s) & 1:
        s = '0' + s
    return bytes().fromhex(s)


def checksum(b):
    '''
    在python2中的循环如下
    for i in re.findall('....', s):
        ret ^= int(i[::-1].encode('hex'), 16)
    校验和以4个字节为一组进行计算，遇到b'\x0a'时，从b'\x0a'之后开始重新分组
    为了能匹配b'\x0a'，不得不加入一个if
    '''
    ret = 1234
    i = 0
    while (i + 4 < len(b)):
        if (not(b[i:i+4].find(b'\x0a') == -1)):
            i = i + b[i:i+4].find(b'\x0a') + 1
        ret ^= int.from_bytes(b[i:i+4][::-1], 'big')
        i = i + 4
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
    print("========================================================================")
    print("-NO-  00 01 02 03 04 05 06 07  08 09 0a 0b 0c 0d 0e 0f  --ascii-string--")
    for i in range(0, len(bytes), 16):
        print("%04x  " % i, end='')
        for j in range(i, i+16):
            if j < len(bytes):
                print("%02x " % bytes[j], end='')
            else:
                print("  ", end='')
            if (j+1) % 8 == 0:
                print(" ", end='')
        print(bytes[i:i+16].decode('ascii', 'replace').replace('\n', '^'))
    print("========================================================================")

