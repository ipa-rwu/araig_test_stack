import rospy
import os
import sys

def getRootFolder():
    DEST_DIR = "/dest_dir"
    ROBOT_TYPE = "/robot_type"
    TEST_TYPE = "/test_type"

    module_name = "/calculators"

    if not rospy.has_param(module_name + DEST_DIR) or rospy.get_param(module_name + DEST_DIR) == "":
        dest_dir = os.path.expanduser("~") + "/ARAIG"
        rospy.logwarn("{} param not set!!, will use {}".format(module_name + DEST_DIR, dest_dir))     
    else:
        dest_dir = rospy.get_param(module_name + DEST_DIR)

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