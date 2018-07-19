#coding=utf-8
import os
import re
import time
import threading
import subprocess
from optparse import OptionParser

import log
from case import TestCase
from case import TestSuite
from connect import ADB, AdbException


def hook(c):
    def deco(f):
        setattr(c, f.__name__, f)
        return f
    return deco

LOGCAT_RUNTEST = [  ('logcat -c;logcat -v threadtime', log.logcat()),
                    ('cat /proc/kmsg', log.kernel()),]

class TextRunner(object):

    def __init__(self, a, option):
        self.a = a
        self.option = option
        self.test_number = 0
        self.report_dir = os.path.join(option.reportdir, 'Logs',option.reportflag, 'report.%s'%time.strftime("%Y_%m_%d.%H_%M_%S",time.localtime(time.time())), 'logs')

        @hook(log)
        def report_directory():
            return self.report_dir
        try:
            os.makedirs(self.report_dir)
        except:
            pass

        try:
            have_procrank = self.a.adbshell('procrank')
            if 'not found' in have_procrank:
                self.a.adb('push tools/procrank /system/xbin/')
                self.a.adbshell('chmod 777 /system/xbin/procrank')
        except:
            log.error('fail to push procrank')

    def startTest(self, test):
        self.a.retry_connection()
        self.a.push(self.option.jarpath)
        self.test_number += 1
        test.id = '%04d' %self.test_number
        test.logDirectory = os.path.join(self.report_dir, test.id)

        @hook(log)
        def log_directory():
            return test.id
        try:
            os.mkdir(test.logDirectory)
        except:
            log.error('mkdir log directory (%s) failed' %test.logDirectory)

        self.clearLog()
        self.running_process = [self.a.popen(command,stdout=open(os.path.join(test.logDirectory,filename), "a+")) for command, filename in LOGCAT_RUNTEST]
        print "running: %s" %(test.uicommand())
        runner = self.a.popen("uiautomator runtest %s" %(test.uicommand()),stdout=open(os.path.join(test.logDirectory, log.uiautomator()),"a+"))
        runner.wait()
        title, steps, runtime, info, output, result = self.__captureResult(os.path.join(test.logDirectory, log.uiautomator()))
        print result,"\n"
        test.title = title
        test.result = result
        test.runtime = runtime
        test.steps += steps
        test.output += output
        if info != []:test.errorinfo = info

        self.__stopTest(test)

    def __stopTest(self, test):
        for p in self.running_process:
            if isinstance(p, subprocess.Popen):
                p.kill()
        self.getLog(test.logDirectory)

    def clearLog(self):
        def isExists(filename):
            ishave = self.a.adbshell('ls %s' %filename)
            if 'No such file or directory' in str(ishave):
                return False
            else:
                return True
        if(isExists('/data/anr')):
            log.debug('rm /data/anr/*')
            self.a.adbshell('rm /data/anr/*')
        if(isExists('/data/tombstones/tombstone_0*')):
            tbs = self.a.adbshell('/data/tombstones/tombstone_0*')
            for tombstone in tbs.splitlines():
                log.debug('rm %s' %tombstone)
                self.a.adbshell('rm %s' %tombstone)
        self.a.adbshell('rm %s/*.png' %log.save_pic_path())

    def getLog(self, path):
        def isExists(filename):
            ishave = self.a.adbshell('ls %s' %filename)
            if 'No such file or directory' in str(ishave):
                return False
            else:
                return True
        if(isExists('/data/Logs/Log.0/anr')):
            os.mkdir(os.path.join(path, 'anr'))
            self.a.adb('pull /data/anr %s' %os.path.join(path, 'anr'))
        if(isExists('/data/tombstones/tombstone_0*')):
            os.mkdir(os.path.join(path, 'tombstones'))
            self.a.adb('pull /data/tombstones %s' %os.path.join(path, 'tombstones'))

        s = self.a.adbshell('ls %s' %(log.save_pic_path()))
        if s != "":
            for pic in s.splitlines():
                self.a.adb('pull %s/%s %s/' %(log.save_pic_path(), pic, path))

    def startSuite(self, suite):
        # add capture meminfo such as `procrank`, `dumpsys meminfo`, `cat /proc/meminfo`, `promen pid` here
        # do not block anything

        self.__flag = True
        t = threading.Thread(target=self.catMeminfo)
        t.setDaemon(True)
        t.start()
        for test in suite.tests:
            self.startTest(test)

        self.__flag = False

    def __captureResult(self, filename):
        """analyze uiautomator log
            return a tuple as (result, info)
            result: PASS or FAIL
            info: [] if PASS otherwise failed info
            output: [] if PASS otherwise output info
        """
        result = "ERROR"
        runtime = "0.000"
        uilog = []
        with open(filename, "rb+") as fp:
            for line in fp:
                # line = line.split('\r\n')
                l = line.strip()
                if l:
                    uilog.append(l)
        for i in range(len(uilog)):
            if uilog[i].startswith("Time:"):
                runtime = uilog[i].strip().split(":")[1]
                if i== len(uilog)-1:
                    result = 'PASS'
                else:
                    if uilog[i+1].startswith("OK"):
                        result = 'PASS'
                    else:
                        result = 'FAIL'
        info = []
        output = []
        title = ""
        steps = []
        for i in range(len(uilog)):
            if uilog[i].startswith('INSTRUMENTATION_STATUS: stack='):
                info.append(uilog[i].rstrip())
            if uilog[i].startswith("INSTRUMENTATION_STATUS: fail file"):
                info.append(uilog[i].rstrip())
            if uilog[i].startswith('INSTRUMENTATION_STATUS_CODE: 15'):
                output.append(uilog[i-1].split("=")[1].rstrip())
            if uilog[i].startswith('INSTRUMENTATION_STATUS_CODE: 16'):
                steps.append(uilog[i-1].split("=")[1].rstrip())
            if uilog[i].startswith('INSTRUMENTATION_STATUS_CODE: 20'):
                title = uilog[i-1].split("=")[1]

        for line in uilog:
            if line.startswith('INSTRUMENTATION_STATUS: stack='):
                info.append(line.rstrip())
            if line.startswith("INSTRUMENTATION_STATUS: fail file"):
                info.append(line.rstrip())
        return title, steps, runtime, list(set(info)), output, result

    def catMeminfo(self):
        while self.__flag:
            self.a.popen('procrank', stdout=open(os.path.join(self.report_dir, log.procrank()), 'a+')).wait()

            self.a.popen('dumpsys meminfo', stdout=open(os.path.join(self.report_dir, log.dumpsys_meminfo()), 'a+')).wait()
            self.a.popen('cat /proc/meminfo', stdout=open(os.path.join(self.report_dir, log.meminfo()), 'a+')).wait()
            self.a.popen('busybox top -n 1', stdout=open(os.path.join(self.report_dir, log.top()), 'a+')).wait()
            time.sleep(log.CAPTURE_MEMINFO_SLEEP_GAP)