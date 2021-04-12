#!/usr/bin/env python
import rospy
import subprocess, shlex
from araig_msgs.msg import BoolStamped, Float64Stamped
import threading
import sys
import os
class BaseLogger(object):
    def __init__(self, sub_dict = {}, result_list = [], param_list = [], rate = 100):
        self._rate = rospy.Rate(rate)

        self._input_interface = {
            "start"           : "/start",
            "stop"            : "/stop",
        }
        self._input_interface.update(sub_dict)
        self._config_param = []
        self._config_param += param_list

        # get ros param:
        self.config_param = {}
        self.getConfig(self._config_param)
        
        self._locks = {}
        self._flag = {}

        for key in self._input_interface:
            rospy.Subscriber(self._input_interface[key], BoolStamped, self.callback, key)
            self._locks[key] = threading.Lock()
            self._flag[key] = BoolStamped()
            self._flag[key].data = False
        
        self.result_list = result_list
        for topic in self.result_list:
            rospy.Subscriber(topic, Float64Stamped, self.callback, topic)
            self._locks[topic] = threading.Lock()
            self._flag[topic] = Float64Stamped()
            self._flag[topic].data = float("inf")
        
        self.pathFolder = self.getRootFolder()

    def setSafeFlag(self, key, value):
        if not key in self._input_interface.keys() and not key in self.result_list:
            rospy.logerr(rospy.get_name() + ": Retrieving a key that does not exist!: {}".format(key))
            return
        with self._locks[key]:
            self._flag[key] = value
    
    def callback(self, msg, key):
        self.setSafeFlag(key,msg)

        # If seq = False, get data; If True, get header
    def getSafeFlag(self, key):
        if not key in self._input_interface.keys() and not key in self.result_list:
            rospy.logerr(rospy.get_name() + ": Retrieving a key that does not exist!: {}".format(key))
            return
        else:
            with self._locks[key]:
                return self._flag[key].data

    def startCommandProc(self, command):
        # Prepare command
        _command = shlex.split(command)
        self.command_proc = subprocess.Popen(_command)
        rospy.loginfo(rospy.get_name() + ": Starting process {} now!".format(self.command_proc))

    def killCommandProc(self):
        self.command_proc.send_signal(subprocess.signal.SIGINT)
        rospy.loginfo(rospy.get_name() + ": Destructor killing process {}!".format(self.command_proc))
    
    def getRootFolder(self):
        DEST_DIR = "/dest_dir"
        ROBOT_TYPE = "/robot_type"
        TEST_TYPE = "/test_type"

        module_name = "/calculators"

        if rospy.has_param(module_name + DEST_DIR):
            dest_dir = rospy.get_param(module_name + DEST_DIR)
        else:
            rospy.logerr("{} param not set!!".format(module_name + DEST_DIR))
            sys.exit()

        if not os.path.exists(dest_dir):    
            rospy.logwarn(rospy.get_name() + ": " + dest_dir + " did not exist, trying to create it. Verify it exists before continuing.")

        if rospy.has_param(module_name + ROBOT_TYPE):
            robot_type = rospy.get_param(module_name + ROBOT_TYPE)
        else:
            rospy.logerr("{} param not set!!".format(module_name + ROBOT_TYPE))
            sys.exit()

        if rospy.has_param(module_name + TEST_TYPE):
            test_type = rospy.get_param(module_name + TEST_TYPE)
        else:
            rospy.logerr("{} param not set!!".format(module_name + TEST_TYPE))
            sys.exit()
        
        path_folder = dest_dir + "/" + robot_type + "/" + test_type + "/"
        return path_folder

    def getSubFolder(self):
        try: 
            size = len(os.listdir(self.pathFolder))
            num = str(size)
            currentFolder = self.pathFolder + num
        except OSError:
            rospy.logerr_once("%s: Can't find the folder: %s", rospy.get_name(), currentFolder)
        return currentFolder
    
    def getConfig(self, param_list):
        for arg in param_list:
            module_name = "/calculators"
            ns = module_name
            if rospy.has_param(ns + arg):
                if arg not in self.config_param:
                    self.config_param[arg] = rospy.get_param(ns + arg)
            else:
                rospy.logerr("{}: {} param not set!!".format(ns, arg))
                rospy.signal_shutdown("param not set")

    def logScreenFile(self, log_msg):
        if self.config_param[rospy.get_name() + "/screen"]:
            rospy.logwarn(rospy.get_name() + ": " + log_msg)
            rospy.loginfo(rospy.get_name() + ": " + log_msg)
        else:
            rospy.loginfo(rospy.get_name() + ": " + log_msg)