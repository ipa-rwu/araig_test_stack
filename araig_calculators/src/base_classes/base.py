import rospy
import os
import sys

def get_root_folder():
    DEST_DIR = "/dest_dir"
    ROBOT_TYPE = "/robot_type"
    TEST_TYPE = "/test_type"

    module_name = "/calculators"

    if not rospy.has_param(module_name + DEST_DIR) or rospy.get_param(module_name + DEST_DIR) == "":
        dest_dir = os.path.expanduser("~") + "/ARAIG"
    else:
        dest_dir = rospy.get_param(module_name + DEST_DIR)

    if not os.path.exists(dest_dir):    
        rospy.logwarn(rospy.get_name() + ": " + dest_dir + " did not exist, trying to create it. Verify it exists before continuing.")

    if rospy.has_param(module_name + ROBOT_TYPE):
        robot_type = rospy.get_param(module_name + ROBOT_TYPE)
    else:
        rospy.logerr("{}: {} param not set!!".format(rospy.get_name(), module_name + ROBOT_TYPE))
        sys.exit()

    if rospy.has_param(module_name + TEST_TYPE):
        test_type = rospy.get_param(module_name + TEST_TYPE)
    else:
        rospy.logerr("{}; {} param not set!!".format(rospy.get_name(), module_name + TEST_TYPE))
        sys.exit()
    
    root = dest_dir + "/" + robot_type + "/" + test_type + "/"
    return root

def check_folder(folder, create = False):
    if os.path.isdir(folder) is False:
        if create is True:
            try:
                os.makedirs(folder) 
                rospy.logwarn("{}: Folder {} is not exist, created it.".format(rospy.get_name(), folder))
                return True
            except OSError:
                rospy.logerr("{}: Folder {} is not exist, But can't create it, Please check if you have right to create.".format(rospy.get_name(), folder))
                return False   
        else:
           rospy.logerr("{}: Folder {} is not exist.".format(rospy.get_name(), folder)) 
    return True

def create_logging_folder(folder):
    if check_folder(folder, True):
        size = len(os.listdir(folder))
    else:
        rospy.logerr("{}: Can't find and create folder {}, Please create it manually.".format(rospy.get_name(), folder))
        sys.exit()
    
    size += 1
    folder_name = folder + str(size)
    try:
        os.mkdir(folder_name)
        rospy.loginfo("{}: Successfully created the directory {}".format(rospy.get_name(), folder_name))
    except OSError as err:
        rospy.logerr("{}: Failed to create {}, error msg: {}".format(rospy.get_name(), folder_name, str(err)))
        sys.exit()

def get_sub_folder():
    root = get_root_folder()
    if check_folder(root):
        num = str(len(os.listdir(root)))
    else:
        rospy.logerr("{}: Can't find folder {}, Please create it manually.".format(rospy.get_name(), root))

    current_folder = root + num
    return current_folder

def create_file(folder, filename):
    with open(folder + "/" + filename, mode='a'): pass