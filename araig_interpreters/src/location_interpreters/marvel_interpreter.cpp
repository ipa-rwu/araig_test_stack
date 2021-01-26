#include "location_interpreters/marvel_interpreter.hpp"

void MarvelInterpreter::hedgeCallback(const marvelmind_nav::hedge_pos_aConstPtr& msg, ros::NodeHandle nh)
{
  int addr = static_cast<int>(msg->address);
  // The map contains pairs of addresses and their assigned publishers
  std::map<int, ros::Publisher>::iterator itr = address_publisher_.find(addr);
  std::string topic_base = ros::this_node::getName() + "/beacon";
  // Check if address already in map
  if(itr == address_publisher_.end())
  {
    // If not, then create a publisher for it and add to map
    ROS_INFO_STREAM(ros::this_node::getName() << " Got new address, adding to map : " <<addr);
    ros::Publisher pub = nh.advertise<geometry_msgs::PoseStamped>(topic_base + std::to_string(addr), 1000, true);
    address_publisher_.insert(std::pair<int, ros::Publisher>(addr, pub));
    checkMap();
  }
  else
  {
    // If yes, then transform the msg to map frame and publish it on the allocated topic
    geometry_msgs::PoseStamped pose;
    pose.header.stamp = ros::Time::now();
    pose.header.frame_id = "/marvel_origin";
    pose.pose.position.x = msg->x_m;
    pose.pose.position.y = msg->y_m;
    pose.pose.position.z = msg->z_m;
    pose.pose.orientation.x = 0;
    pose.pose.orientation.y = 0;
    pose.pose.orientation.z = 0;
    pose.pose.orientation.w = 1;


    geometry_msgs::PoseStamped pose_in_map_frame;
    while  (!tf_listener_.waitForTransform("/map", 
            "/marvel_origin", 
            ros::Time::now(),
            ros::Duration(0.01)));

    try {
      tf_listener_.transformPose("/map",pose,pose_in_map_frame);
    } catch (tf::ExtrapolationException e) {
    }

    itr->second.publish(pose_in_map_frame);

    // and also publish the frame on TF
    geometry_msgs::TransformStamped transformStamped;

    transformStamped.header.stamp = ros::Time::now();
    transformStamped.header.frame_id = "/marvel_origin";

    transformStamped.child_frame_id = "/beacon" + std::to_string(itr->first);
    transformStamped.transform.translation.x = msg->x_m;
    transformStamped.transform.translation.y = msg->y_m;
    transformStamped.transform.translation.z = msg->z_m;
    tf2::Quaternion q;
    q.setRPY(0, 0, 0);
    transformStamped.transform.rotation.x = q.x();
    transformStamped.transform.rotation.y = q.y();
    transformStamped.transform.rotation.z = q.z();
    transformStamped.transform.rotation.w = q.w();

    tf_broadcaster_.sendTransform(transformStamped);
  }
}


MarvelInterpreter::MarvelInterpreter()
{

}

void MarvelInterpreter::checkMap()
{
  if (address_publisher_.empty())
  {
    ROS_ERROR_STREAM(ros::this_node::getName() << "Publisher map is empty!!");
    ros::shutdown();
  }
  ROS_INFO_STREAM(ros::this_node::getName() << " Publishing on following topics:");
  for(std::map<int, ros::Publisher>::iterator itr = address_publisher_.begin(); itr!= address_publisher_.end(); itr++)
  {
    ROS_INFO_STREAM(ros::this_node::getName() << " Beacon " << itr->first << " on " << itr->second.getTopic() );
  }
}

int main(int argc, char **argv)
{
  ros::init(argc, argv, "marvel_location_interpreter");
  ros::NodeHandle nh;

  MarvelInterpreter interpreter;

  ros::Duration(1).sleep(); //Wait for tf buffer to fill up
  interpreter.sub_beacon_pos_ = nh.subscribe<marvelmind_nav::hedge_pos_a>("/hedge_pos_a", 10,
                                             boost::bind( &MarvelInterpreter::hedgeCallback, &interpreter, _1, nh));

  ros::Rate loop_rate(100);
  while (ros::ok())
  {
    ros::spinOnce();
    loop_rate.sleep();
  }

  return 0;
}
