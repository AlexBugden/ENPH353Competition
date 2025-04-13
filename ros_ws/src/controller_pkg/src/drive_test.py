#!/usr/bin/env python3
from __future__ import print_function

import sys
import rospy
import cv2
from geometry_msgs.msg import Twist
from rosgraph_msgs.msg import Clock
from sensor_msgs.msg import Image
from std_msgs.msg import String
from cv_bridge import CvBridge, CvBridgeError

class image_converter:
    def __init__(self):
        # Initialize the CvBridge to convert ROS images to OpenCV format
        self.bridge = CvBridge()
        
        # Subscribe to the camera image topic
        self.image_sub = rospy.Subscriber("/B1/rrbot/camera1/image_raw", Image, self.image_callback)
        
        # Subscribe to the /clock topic
        self.clock_sub = rospy.Subscriber("/clock", Clock, self.clock_callback)
        
        # Publisher for velocity commands
        self.vel_pub = rospy.Publisher("/B1/cmd_vel", Twist, queue_size=1)
        
        # Publisher for the /score_tracker topic
        self.score_pub = rospy.Publisher("/score_tracker", String, queue_size=1)
        
        # Variables for timer and robot control
        self.start_time = None
        self.timer_started = False  # Initialize timer_started here
        self.first_image_received = False
        self.elapsed_time = 0.0
        self.team_name = "TeamName"  # Replace with your team name
        self.password = "password"   # Replace with your password


    ## @brief Callback function for the /clock topic.
    #  @param data The incoming Clock message.
    def clock_callback(self, data):
        # Check if timer_started is initialized
        if not hasattr(self, 'timer_started'):
            rospy.logwarn("timer_started not initialized yet. Skipping clock_callback.")
            return
        
        # Get the current time from the /clock topic
        current_time = data.clock
        
        # If the timer has started, check if 5 seconds have passed
        if self.timer_started:
           self.elapsed_time = (current_time - self.start_time).to_sec()
           ## if self.elapsed_time >= 50.0:  # Stop after 5 seconds
               ## self.stop_robot()
               ## rospy.loginfo("Timer stopped at: %.2f seconds", current_time.to_sec())
               ## rospy.loginfo("Elapsed time: %.2f seconds", self.elapsed_time)
               ## rospy.signal_shutdown("Task completed")  # Shutdown the node

    ## @brief Callback function for the camera image topic.
    #  @param data The incoming Image message.
    def image_callback(self, data):
        # if self.elapsed_time >= 50.0:
           ## self.stop_robot2()
           ## return
        
        # Start the timer and robot on the first call to this function
        if not self.first_image_received:
            self.first_image_received = True
            self.start_timer()
        if self.elapsed_time < 1.0:
            return
        try:
            # Convert the ROS Image message to an OpenCV grayscale image
            cv_image = self.bridge.imgmsg_to_cv2(data, "mono8")
        except CvBridgeError as e:
            rospy.logerr("CvBridge Error: %s", e)
            return
        
        # Process the image (e.g., detect a line)
        err = 5  # Placeholder for error calculation
        self.publish_velocity(err)

    ## @brief Starts the timer by storing the current time.
    def start_timer(self):
        
        # Wait for the first clock message to initialize the start time
        rospy.loginfo("Waiting for /clock topic to be available...")
        try:
            rospy.wait_for_message("/clock", Clock, timeout=10.0)  # Wait for /clock with a timeout
            self.start_time = rospy.Time.now()
            self.timer_started = True
            rospy.loginfo("Timer started at: %.2f seconds", self.start_time.to_sec())
        except rospy.ROSException as e:
            rospy.logerr("Failed to initialize timer: %s", e)
            return
        
        rospy.sleep(1)

        # Publish a message to /score_tracker to start the competition timer
        start_msg = f"{self.team_name},{self.password},0,NA"
        retry_count = 3  # Retry mechanism
        for attempt in range(retry_count):
            # Check if there are subscribers to /score_tracker
            if self.score_pub.get_num_connections() > 0:
                self.score_pub.publish(start_msg)
                rospy.loginfo("Published start message to /score_tracker: %s", start_msg)
                break  # Exit loop after successful publish
            else:
                rospy.logwarn(f"No subscribers to /score_tracker. Retrying... (Attempt {attempt + 1}/{retry_count})")
                rospy.sleep(0.5)  # Wait before retrying

    ## @brief Stops the robot by publishing a zero velocity command.
    def stop_robot(self):
        vel_msg = Twist()
        vel_msg.linear.x = 0.0  # Stop the robot
        vel_msg.angular.z = 0.0  # No turning
        self.vel_pub.publish(vel_msg)
        rospy.loginfo("Robot stopped")

        # Publish a message to /score_tracker to stop the competition timer
        stop_msg = f"{self.team_name},{self.password},-1,NA"
        self.score_pub.publish(stop_msg)
        rospy.loginfo("Published stop message to /score_tracker: %s", stop_msg)
    
    ## @brief Stops the robot by publishing a zero velocity command.
    def stop_robot2(self):
        vel_msg = Twist()
        vel_msg.linear.x = 0.0  # Stop the robot
        vel_msg.angular.z = 0.0  # No turning
        self.vel_pub.publish(vel_msg)
        rospy.loginfo("Robot stopped 2")

    ## @brief Publishes velocity commands based on the detected line position error.
    #  @param error The difference between the line position and the center of the image.
    def publish_velocity(self, error):
        if self.elapsed_time < 1.0:
            return
        if self.elapsed_time > 1.0 and self.elapsed_time < 3.0:
            rospy.sleep(0.2)
            vel_msg = Twist()
            vel_msg.linear.x = 5  # Constant forward speed
            vel_msg.angular.z = 0  # Proportional control for steering
            self.vel_pub.publish(vel_msg)
        if self.elapsed_time > 3.0 and self.elapsed_time < 5.0:
            vel_msg = Twist()
            vel_msg.linear.x = 0
            vel_msg.angular.z = 0
            self.vel_pub.publish(vel_msg)
        if self.elapsed_time > 5.0 and self.elapsed_time < 7.0:
            vel_msg = Twist()
            vel_msg.linear.x = 0.7
            vel_msg.angular.z = 0
            self.vel_pub.publish(vel_msg)
        if self.elapsed_time > 7.0 and self.elapsed_time < 9.0:
            vel_msg = Twist()
            vel_msg.linear.x = 0
            vel_msg.angular.z = -1.8
            self.vel_pub.publish(vel_msg)
        if self.elapsed_time > 9.0:
            vel_msg = Twist()
            vel_msg.linear.x = 0
            vel_msg.angular.z = 0
            self.vel_pub.publish(vel_msg)

## @brief Main function to initialize the ROS node and start the image processing.
#  @param args Command-line arguments.
def main(args):
    # Initialize the ROS node
    rospy.init_node('image_converter', anonymous=True)
    
    # Create an instance of the image converter class
    ic = image_converter()
    
    try:
        # Keep the node running
        rospy.spin()
    except KeyboardInterrupt:
        rospy.loginfo("Shutting down")
    
    # Destroy any OpenCV windows
    cv2.destroyAllWindows()

if __name__ == '__main__':
    main(sys.argv)
