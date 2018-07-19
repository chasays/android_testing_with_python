#coding=utf-8
import re
import time
import subprocess
import log

class AdbException(Exception):
    def __init__(self, message):
        Exception.__init__(self, message+'\n')

RETRY_CONNECTION_TIMES = 5
RETRY_CONNECTION_BETWEEN = 10

class ADB(object):
    def __init__(self, id):
        self.id = id.rstrip()
        log.debug('target devices: %s' %self.id)
        self.adbd = 'adb'
        #check adb is installed
        try:
            subprocess.Popen( [ self.adbd, 'devices' ], stdout=subprocess.PIPE,stderr=subprocess.STDOUT).stdout.read(1)
            self.adb_command = [self.adbd]
        except:
            raise AdbException("Error: is `adb` installed ??")

        self.__isNetworkConnection()
        self.adb_command = [ self.adbd, '-s', self.id ]
        self.adbsh_command = [ self.adbd, '-s', self.id, 'shell' ]
        self.retry_connection()

    def retry_connection(self):
        while not self._connection():
            print 'Retry Connection'
            time.sleep(RETRY_CONNECTION_BETWEEN)

    def _connection(self):
        devices = self.__adb('devices')

        if not str(devices).__contains__(self.id):
            # self.adb('disconnect')
            r = self.__adb('connect %s' %self.id.split(":")[0] if ":" in self.id else self.id)
            if str(r).__contains__('unable to connect to'):
                print 'unable to connect to %s' %self.id
                return False
            time.sleep(1)

        r = self.adb('root')
        log.debug('root devices:\n %s' %r)
        if 'adbd is already running as root' not in r:
            time.sleep(2)
            self.__adb('connect %s' %self.id.split(":")[0] if ":" in self.id else self.id)
            time.sleep(1)
        self.adb('remount')
        log.debug('remount devices:\n %s' %r)
        return True

    def __adb(self, command):
        if not isinstance(command, list): command = command.split()
        log.debug(str([self.adbd] + command))
        return subprocess.Popen([self.adbd]+command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT).communicate()[0]

    def adb(self, command):
        """ run `adb -s serial` command """
        if not isinstance(command, list): command = command.split()
        log.debug(str(self.adb_command + command))
        return subprocess.Popen(self.adb_command + command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT).communicate()[0]

    def adbshell(self, command):
        """ run `adb -s serial shell` command """
        if not isinstance(command, list): command = command.split()
        log.debug(str(self.adbsh_command + command))
        return subprocess.Popen(self.adbsh_command + command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT).communicate()[0]

    def popen(self, cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT):
        """run adb shell command as nohup, return subprocess.Popen instance"""
        if not isinstance(cmd, list): cmd = [cmd]
        log.debug("popen command: "+str(self.adbsh_command+cmd))
        return subprocess.Popen(self.adbsh_command+cmd, stdout=stdout,stderr=stderr)

    def screenshot(self, filename, path="/data/local/tmp"):
        self.adbshell("screencap -p %s" %os.path.join(path,filename, ".png"))

    def push(self, jar, path="/data/local/tmp"):
        #95 KB/s (6332 bytes in 0.064s)
        r = self.adb("push %s %s/" %(jar, path))
        pflag = False
        for _retry_times in range(1,6):
            if re.compile(r'\d+ KB/s \(\d+ bytes in .*s\)').match(r):
                pflag = True
                break;
            print r
            self.retry_connection()
            r = self.adb("push %s %s/" %(jar, path))
        if not pflag: raise AdbException(r)

    def install(self, apkname):
        #2685 KB/s (2433480 bytes in 0.884s)
        #    pkg: /data/local/tmp/Settings.apk
        #Success
        r = self.adb("install -r %s" %apkname)
        pflag = False
        for _retry_times in range(1,6):
            if str(r).__contains__('Success'):
                pflag = True
                break;
            print r
            self.retry_connection()
            r = self.adb("push %s %s/" %(jar, path))
        if not pflag: raise AdbException(r)