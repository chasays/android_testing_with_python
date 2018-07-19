#coding=utf-8
import os
from optparse import OptionParser
import core as ucore

def main():
    parse = OptionParser()
    parse.add_option('-f', '--file', dest='listfile', help='case or list to run', action='store')
    parse.add_option('-s', '--serial', dest='serialno', help='which device to run', action='store')
    parse.add_option('-c', '--count', dest='count', help='how many times to run', action='store', default='1')
    parse.add_option('-r', '--reportdir', dest='reportdir', help='where to capture report', action='store', default=".")
    parse.add_option('-j', '--jar', dest='jarpath', help='which jar to run', action='store')

    (option, args) = parse.parse_args()

    a = ucore.ADB(option.serialno)
    attribute = a.adbshell('getprop')

    if option.serialno == None:
        raise ucore.AdbException('Error: MUST specify a serial number!')
    count = int(option.count)
    suite = ucore.TestSuite()
    for i in range(count):
        suite.addTestCase(option.listfile)

    #start test
    runner = ucore.TextRunner(a, option)
    runner.startSuite(suite)

    print '\nLog Directory: %s \n' %os.path.dirname(runner.report_dir)

if __name__ == '__main__':
    main()