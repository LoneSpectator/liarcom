#coding=UTF-8

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