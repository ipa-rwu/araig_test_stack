#!/usr/bin/env python
import rospy
from araig_msgs.msg import BoolStamped
import yaml
import os
import threading

class TestBase(object):
    def __init__(self, sub_dict = {} , pub_dict = {}, param_list = {}, rate = 100):      

        self._rate = rospy.Rate(rate)

        self._input_interface = {
            "robot_has_stopped"    : "/signal/calc/robot_has_stopped",
            "start_test"           : "/signal/ui/start_test",
            "interrupt_test"       : "/signal/ui/interrupt_test",
            "reset_test"           : "/signal/ui/reset_test"
        }
        self._input_interface.update(sub_dict)
        self._output_interface = {
            "start_robot"           : "/signal/runner/start_robot",
            "test_completed"        : "/signal/runner/test_completed",
            "test_failed"           : "/signal/runner/test_failed",
            "test_succeeded"        : "/signal/runner/test_succeeded",
            "start_test"            : "/signal/ui/start_test",
            "reset_test"            : "/signal/ui/reset_test",
            "interrupt_test"        : "/signal/ui/interrupt_test"
        }
        self._output_interface.update(pub_dict)
        self._config_param = []
        self._config_param += param_list

        self._locks = {}
        self._flag = {}
        self._publishers = {}

        # get ros param:
        self.config_param = {}
        self.get_config(self._config_param)

        # sub_init
        for key in self._input_interface:
            rospy.Subscriber(self._input_interface[key], BoolStamped, self.callback_for_all_bool_topics, key)
            self._locks[key] = threading.Lock()
            self._flag[key] = BoolStamped()
            self._flag[key].data = False
        # pub_init
        for key in self._output_interface:
            self._publishers[key] = rospy.Publisher(self._output_interface[key], BoolStamped,queue_size=10, latch=True)

        try:
            while not rospy.is_shutdown():
                self.main() 
                self._rate.sleep()
        except rospy.ROSException:
            pass

    def setSafeFlag(self, key, value):
        if not key in self._input_interface.keys():
            rospy.logerr(rospy.get_name() + ": Retrieving a key that does not exist!: {}".format(key))
            return
        with self._locks[key]:
            self._flag[key] = value
    
    # If seq = False, get data; If True, get header
    def getSafeFlag(self, key, header = False):
        if not key in self._input_interface.keys():
            rospy.logerr(rospy.get_name() + ": Retrieving a key that does not exist!: {}".format(key))
            return
        else:
            with self._locks[key]:
                if not header:
                    return self._flag[key].data
                else:
                    return self._flag[key].header
    
    def buildNewBoolStamped(self, data = True):
        msg = BoolStamped()
        msg.header.stamp = rospy.Time.now()
        msg.data = data
        return msg

    def callback_for_all_bool_topics(self, msg, key):
        self.setSafeFlag(key,msg)

    def startRecordingAndWait(self, duration=3):
        rospy.loginfo(rospy.get_name() + ": waiting for {}s, then start recoding ...".format(duration))
        rospy.sleep(duration)

    def timestampToFloat(self, stamp):
        timestamp_float =  float(stamp.secs + float(stamp.nsecs*(1e-9)))
        return timestamp_float

    def checkCondition(self, start_timestamp, duration):
        if self.timestampToFloat(rospy.Time.now() - start_timestamp) <= duration:
            return False
        else:
            return True
    
    def get_config(self, param_list):
        for arg in param_list:
            module_name = "/runner/"
            ns = module_name
            if rospy.has_param(ns + arg):
                self.config_param[arg] = rospy.get_param(ns + arg)
            else:
                rospy.logerr("{}: {} param not set!!".format(ns, arg))
                rospy.signal_shutdown()
    
    def main(self):
        pass
