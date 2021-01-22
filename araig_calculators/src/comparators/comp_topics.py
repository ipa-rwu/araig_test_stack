#!/usr/bin/env python
from multipledispatch import dispatch as Override
import rospy

from base_classes.base_calculator import BaseCalculator
from araig_msgs.msg import BoolStamped

"""Compare data from two topics, output data_type: bool
    pub_dict = {"/signal": BoolStamped}
    sub_dict = {"topic_1": "data_type", "topic_2": "data_type"}
    inherit Base, only modify compare function""" 
class compTopics(BaseCalculator):
    _sub_topic_1 = "/in_bool_1"
    _sub_topic_2 = "/in_bool_2"
    _pub_topic = "/out_bool"
    def __init__(self,
            sub_dict = {_sub_topic_1: BoolStamped, 
                        _sub_topic_2: BoolStamped},
            pub_dict = {_pub_topic: BoolStamped},
            rate = None,
            tolerance = 0):

            if sub_dict == None or len(sub_dict) < 2:
                rospy.logerr("{}:  Please provide two topics to subscribe".format(rospy.get_name()))
            self.tolerance = tolerance
            self.pre_state = None

            super(compTopics, self).__init__(
                sub_dict = sub_dict,
                pub_dict = pub_dict,
                rate = rate)

    @Override()
    def calculate(self):
        temp = {}
        msg = self.PubDict[self._pub_topic]()

        flag_test_ready = True
        for topic in self.SubDict.keys():
            with BaseCalculator.LOCK[topic]:
                temp[topic] = BaseCalculator.MSG[topic]
            if temp[topic] == None:
                flag_test_ready = False
        
        if flag_test_ready == True:
            msg.header.stamp = rospy.Time.now()
            if temp[self._sub_topic_1].data == True and \
                temp[self._sub_topic_2].data == True:
                msg.data = True
            else:
                msg.data = False

            if self.pub_only_state_change(pre_state = self.pre_state, \
                current_state = msg.data, \
                pub_topic = self._pub_topic, \
                pub_msg = msg,
                log = "{}: {}".format(rospy.get_name(), msg.data)):
                self.pre_state = msg.data