cmake_minimum_required(VERSION 3.0.2)
project(vrx_controller_ros)

find_package(catkin REQUIRED COMPONENTS geographic_msgs nav_msgs rospy robot_localization std_msgs)

catkin_package()

catkin_install_python(PROGRAMS
  scripts/station_keeping_node.py
  scripts/trial_monitor.py
  DESTINATION ${CATKIN_PACKAGE_BIN_DESTINATION}
)

install(DIRECTORY launch config
  DESTINATION ${CATKIN_PACKAGE_SHARE_DESTINATION}
)
