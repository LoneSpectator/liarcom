#coding=UTF-8

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

    