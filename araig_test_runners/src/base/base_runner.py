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
            "stop_robot"            : "/signal/runner/stop_robot",
            "test_completed"        : "/signal/runner/test_completed",
            "test_failed"           : "/signal/runner/test_failed",
            "test_succeeded"        : "/signal/runner/test_succeeded",
            # TODO: The next 3 signals should be removed once UI is fully integrated
            "start_test"            : "/signal/ui/start_test",
            "reset_test"            : "/signal/ui/reset_test",
            "interrupt_test"        : "/signal/ui/interrupt_test"
        }
        self._output_interface.update(pub_dict)
        self._config_param = [
            "start_logging_offset",
            ]
        self._config_param += param_list

        # TODO: Make this enums or constants or something
        self._RETURN_CASE_INTERRUPTED = -1
        self._RETURN_CASE_TIMED_OUT = -2

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
            self._publishers[key].publish(self.buildNewBoolStamped(False))

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

    def timestampToFloat(self, stamp):
        timestamp_float =  float(stamp.secs + float(stamp.nsecs*(1e-9)))
        return timestamp_float

    def get_config(self, param_list):
        for arg in param_list:
            module_name = "/runner/"
            ns = module_name
            if rospy.has_param(ns + arg):
                self.config_param[arg] = rospy.get_param(ns + arg)
            else:
                rospy.logerr("{}: {} param not set!!".format(ns, arg))
                rospy.signal_shutdown("Param not set")

    def isInterrupted(self):
        if self.getSafeFlag("interrupt_test"):
            rospy.logwarn(rospy.get_name() + ": Interrupted! Test failed! Stopping robot!")
            self.stopRobot()
            self.testFailed()
            self.waitForReset()
            return True

    # Every test needs to override this function with core logic
    def main(self):
        pass

    # The following functions impart a standard interface/structure to every runner
    # but can also be overriden with test specific logic in subclasses
    def startRobot(self):
        # Expectation: Velocity interpreter starts sending cmd_vel, Goal interpreter calls move_base action with goal etc..
        self._publishers["stop_robot"].publish(self.buildNewBoolStamped(False))
        rospy.sleep(0.1)
        self._publishers["start_robot"].publish(self.buildNewBoolStamped(True))

    def stopRobot(self):
        # Expectation: Velocity interpreter stops sending cmd_vel, Goal interpreter calls move_base action cancel etc..
        self._publishers["start_robot"].publish(self.buildNewBoolStamped(False))
        rospy.sleep(0.1)
        self._publishers["stop_robot"].publish(self.buildNewBoolStamped(True))

    def standardStartupSequence(self):
        # Wait until start signal received
        rospy.logwarn(rospy.get_name() + ": Waiting to start...")
        self.loopFallbackOnFlags(["start_test"])
        # Start received, wait for recorders to boot up. Cannot be interrupted.
        rospy.logwarn(rospy.get_name() + ": Start received, waiting {}s for recorder init"
                        .format(self.config_param['start_logging_offset']))
        self.sleepUninterruptedFor(self.config_param['start_logging_offset'])
        # Start robot
        rospy.logwarn(rospy.get_name() + ": Starting robot")
        self.startRobot()

    def testCompleted(self):
        self.stopRobot()
        self._publishers["test_completed"].publish(self.buildNewBoolStamped(True))

    def testSucceeded(self):
        self.testCompleted()
        self._publishers["test_succeeded"].publish(self.buildNewBoolStamped(True))
        self._publishers["test_failed"].publish(self.buildNewBoolStamped(False))

    def testFailed(self):
        self.testCompleted()
        self._publishers["test_failed"].publish(self.buildNewBoolStamped(True))
        self._publishers["test_succeeded"].publish(self.buildNewBoolStamped(False))

    # TODO: These functions can eventually be used as "nodes" in a Behaviour Tree like structure
    def waitForReset(self):
        rospy.logwarn("----------------------------------------------------------")
        rospy.logwarn(rospy.get_name() + ": Waiting for user to give reset signal")
        rospy.logwarn("----------------------------------------------------------")

        # TODO: ui should set reset_test to False after set to True, reset signal is an event 
        while not self.getSafeFlag("reset_test"): 
            self._rate.sleep()
        rospy.logwarn(rospy.get_name() + ": Resetting")
        for key in self._output_interface:
            self._publishers[key].publish(self.buildNewBoolStamped(False))

    def sleepUninterruptedFor(self, duration):
        start = rospy.Time.now()
        while self.timestampToFloat(rospy.Time.now() - start) <= duration:
            self._rate.sleep()
            if self.isInterrupted():
                return self._RETURN_CASE_INTERRUPTED

    # Returns the first flag that is true, or if interrupted
    def loopFallbackOnFlags(self, flag_list = []):
        while not self.isInterrupted():
            self._rate.sleep()
            for index, flag in enumerate(flag_list):
                if self.getSafeFlag(flag):
                    return index
        return self._RETURN_CASE_INTERRUPTED

    # Returns the first flag that is false, or if interrupted
    def loopSequenceOnFlags(self, flag_list = []):
        while not self.isInterrupted():
            self._rate.sleep()
            for index, flag in enumerate(flag_list):
                if not self.getSafeFlag(flag):
                    return index
        return self._RETURN_CASE_INTERRUPTED

    # Returns the first flag that is true, or if interrupted, or if timed out
    def timedLoopFallbackOnFlags(self, flag_list, duration):
        start = rospy.Time.now()
        while not self.isInterrupted():
            self._rate.sleep()
            if self.timestampToFloat(rospy.Time.now() - start) > duration:
                return self._RETURN_CASE_TIMED_OUT
            for index, flag in enumerate(flag_list):
                if self.getSafeFlag(flag):
                    return index
        return self._RETURN_CASE_INTERRUPTED

    # Returns the first flag that is false, or if interrupted, or if timed out
    def timedLoopSequenceOnFlags(self, flag_list, duration):
        start = rospy.Time.now()
        while not self.isInterrupted():
            self._rate.sleep()
            if self.timestampToFloat(rospy.Time.now() - start) > duration:
                return self._RETURN_CASE_TIMED_OUT
            for index, flag in enumerate(flag_list):
                if not self.getSafeFlag(flag):
                    return index
        return self._RETURN_CASE_INTERRUPTED
