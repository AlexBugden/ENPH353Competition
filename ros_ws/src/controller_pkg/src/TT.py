#!/usr/bin/env python3
from __future__ import print_function

import sys
import rospy
import cv2
import numpy as np
from PIL import Image as PILImage
from ultralytics import YOLO
from tensorflow.keras.models import load_model
from geometry_msgs.msg import Twist
from rosgraph_msgs.msg import Clock
from sensor_msgs.msg import Image
from std_msgs.msg import String
from cv_bridge import CvBridge, CvBridgeError
from gazebo_msgs.srv import SetModelState
from gazebo_msgs.msg import ModelState

# Add your image processing code as class methods
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
        self.timer_started = False
        self.first_image_received = False
        self.elapsed_time = 0.0
        self.team_name = "Team12"
        self.password = "password"
        # Variables to store processing results
        self.current_id = None
        self.current_message = None
        self.last_processed_time = 0
        self.processing_interval = 1.0  # Process images every 2 seconds
        self.seen_ids = set()  # Store detected IDs
        self.port1 = False
        self.port2 = False
        self.port3 = False
        self .stopped = False

                # Special words mapping
        self.special_words = {
            'SIZE': 1, 'VICTIM': 2, 'CRIME': 3, 'TIME': 4,
            'PLACE': 5, 'MOTIVE': 6, 'WEAPON': 7, 'BANDIT': 8
        }
        
        # Class to letter mapping
        self.class_to_letter = {
            0: 'A', 1: 'B', 2: 'C', 3: 'D', 4: 'E',
            5: 'F', 6: 'G', 7: 'H', 8: 'I', 9: 'J',
            10: 'K', 11: 'L', 12: 'M', 13: 'N', 14: 'O',
            15: 'P', 16: 'R', 17: 'S', 18: 'T', 19: 'U',
            20: 'V', 21: 'W', 22: 'X', 23: 'Y', 24: 'Z',
            25: '2', 26: '5', 27: '8', 28: '9'
        }
        
        
        # Initialize your models
        self.yolo_model = YOLO("best.pt")  # Load YOLO model
        self.char_model = load_model("character_rec.keras")  # Load character recognition model
        
    def spawn_position(self, position):
        """Set the position and orientation of 'B1' in Gazebo."""
        msg = ModelState()
        msg.model_name = 'B1'

        msg.pose.position.x = position[0]
        msg.pose.position.y = position[1]
        msg.pose.position.z = position[2]
        msg.pose.orientation.x = position[3]
        msg.pose.orientation.y = position[4]
        msg.pose.orientation.z = position[5]
        msg.pose.orientation.w = position[6]

        rospy.wait_for_service('/gazebo/set_model_state')
        try:
            set_state = rospy.ServiceProxy('/gazebo/set_model_state', SetModelState)
            resp = set_state(msg)
            rospy.loginfo("Model 'B1' repositioned successfully.")
        except rospy.ServiceException:
            rospy.logerr("Service call to set model state failed")

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
            #if self.elapsed_time >= 50.0:  # Stop after 5 seconds
                #self.stop_robot()
                #position = [0, 0, 0, 0, 0, 0, 1]
                #self.spawn_position(position)
                #rospy.loginfo("Robot stopped at 50 seconds")
                #rospy.loginfo("Timer stopped at: %.2f seconds", current_time.to_sec())
                #rospy.loginfo("Elapsed time: %.2f seconds", self.elapsed_time)
                #rospy.signal_shutdown("Task completed")  # Shutdown the node





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

    
    def prepare_image_for_prediction(self, img_array):
        """Prepare image array for prediction"""
        img_resized = cv2.resize(img_array, (256, 183))
        img_normalized = img_resized / 255.0
        return np.expand_dims(img_normalized, axis=0)
    
    def order_points(self, pts):
        """Orders the points in consistent order"""
        rect = np.zeros((4, 2), dtype="float32")
        s = pts.sum(axis=1)
        rect[0] = pts[np.argmin(s)]
        rect[2] = pts[np.argmax(s)]
        diff = np.diff(pts, axis=1)
        rect[1] = pts[np.argmin(diff)]
        rect[3] = pts[np.argmax(diff)]
        return rect
    
    def process_image(self, image, min_box_area=200000):
        """Process image to find and transform largest blue box"""
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        lower_blue = np.array([102, 124, 80])
        upper_blue = np.array([140, 255, 255])
        mask = cv2.inRange(hsv, lower_blue, upper_blue)
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if not contours:
            return None
        
        largest_contour = max(contours, key=cv2.contourArea)
        contour_area = cv2.contourArea(largest_contour)
        
        if contour_area < min_box_area:
            return None
        
        epsilon = 0.02 * cv2.arcLength(largest_contour, True)
        approx = cv2.approxPolyDP(largest_contour, epsilon, True)
        
        if len(approx) == 4:
            pts_src = np.array([point[0] for point in approx], dtype="float32")
            ordered_pts = self.order_points(pts_src)
            width, height = 300, 150
            pts_dst = np.array([
                [0, 0], [width - 1, 0],
                [width - 1, height - 1], [0, height - 1]
            ], dtype="float32")
            M = cv2.getPerspectiveTransform(ordered_pts, pts_dst)
            return cv2.warpPerspective(image, M, (width, height))
        return None
    
    def remove_blue_border(self, image):
        """Remove blue border from image"""
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        lower_blue = np.array([0, 2, 0])
        upper_blue = np.array([255, 255, 255])
        mask = cv2.inRange(hsv, lower_blue, upper_blue)
        mask_inv = cv2.bitwise_not(mask)
        kernel = np.ones((3,3), np.uint8)
        mask_inv = cv2.morphologyEx(mask_inv, cv2.MORPH_CLOSE, kernel, iterations=2)
        contours, _ = cv2.findContours(mask_inv, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if contours:
            x, y, w, h = cv2.boundingRect(np.concatenate(contours))
            return image[y:y+h, x:x+w]
        return image
    
    def process_words(self, image):
        """Process image to detect words and return letters grouped by words"""
        results = self.yolo_model(image)
        word_groups = []
        
        for result in results:
            sorted_boxes = sorted(result.boxes.xyxy, key=lambda box: box[0])
            
            for box in sorted_boxes:
                x1, y1, x2, y2 = map(int, box)
                word_crop = image[y1:y2, x1:x2]
                word_letters = []
                
                gray = cv2.cvtColor(word_crop, cv2.COLOR_BGR2GRAY)
                _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
                vertical_projection = np.sum(thresh, axis=0)
                
                                # Letter segmentation logic
                in_gap = False
                gap_start = 0
                split_positions = []

                # Find gaps between letters
                for pos, value in enumerate(vertical_projection):
                    if value == 0 and not in_gap:
                        in_gap = True
                        gap_start = pos
                    elif value > 0 and in_gap:
                        in_gap = False
                        if pos - gap_start > 1:  # Minimum gap threshold
                            split_positions.append((gap_start + pos) // 2)  # Middle of gap

                # Add start and end positions if no letters detected
                if not split_positions:
                    split_positions = [0, word_crop.shape[1]]
                else:
                    split_positions = [0] + split_positions + [word_crop.shape[1]]

                # Split word into individual letters
                for k in range(len(split_positions)-1):
                    letter_x1 = split_positions[k]
                    letter_x2 = split_positions[k+1]
                    
                    # Only consider segments wider than 5 pixels
                    if letter_x2 - letter_x1 >= 5:
                        letter_img = word_crop[:, letter_x1:letter_x2]
                        
                        # Add padding if needed (maintains aspect ratio for CNN)
                        pad_width = max(0, (letter_img.shape[0] - letter_img.shape[1]) // 2)
                        if pad_width > 0:
                            letter_img = cv2.copyMakeBorder(letter_img, 0, 0, pad_width, pad_width, 
                                                         cv2.BORDER_CONSTANT, value=[255,255,255])
                        
                        word_letters.append(letter_img)
                
                word_groups.append(word_letters)
        
        return word_groups
    
    def find_special_word(self, word):
        """Check if word matches any special word with 1 character substitution"""
        word = word.upper()
        for special in self.special_words:
            if len(word) == len(special):
                diff_count = sum(1 for a, b in zip(word, special) if a != b)
                if diff_count <= 1:
                    return special
        return None
    
    def process_ros_image(self, cv_image):
        """Process ROS image through your pipeline"""
        # Convert mono to color if needed
        if len(cv_image.shape) == 2:
            cv_image = cv2.cvtColor(cv_image, cv2.COLOR_GRAY2BGR)
        
        # Step 1: Process image to find and transform blue box
        transformed = self.process_image(cv_image)
        if transformed is None:
            return None, None
        
        # Step 2: Remove blue border
        cleaned = self.remove_blue_border(transformed)
        
        # Step 3: Process words
        word_groups = self.process_words(cleaned)
        
        # Step 4: Recognize letters
        recognized_words = []
        for word_letters in word_groups:
            word_text = []
            for letter_img in word_letters:
                pil_img = PILImage.fromarray(cv2.cvtColor(letter_img, cv2.COLOR_BGR2RGB))
                prepared = self.prepare_image_for_prediction(np.array(pil_img))
                if prepared is not None:
                    prediction = self.char_model.predict(prepared)
                    predicted_idx = np.argmax(prediction)
                    mapped_letter = self.class_to_letter.get(predicted_idx, '?')
                    print(f"Predicted Index: {predicted_idx}, Mapped Letter: {mapped_letter}")
                    word_text.append(mapped_letter)

            recognized_words.append(''.join(word_text))
        
        # Step 5: Find special word and message
        id = None
        message_words = []
        for word in recognized_words:
            special_word = self.find_special_word(word)
            if special_word and id is None:
                id = self.special_words[special_word]
            else:
                message_words.append(word)
        
        return id, ' '.join(message_words) if message_words else None
    
    def image_callback(self, data):
        # Timer/robot control logic (from original)
        #if self.elapsed_time >= 50.0:
            #self.stop_robot2()
            #position = [0, 0, 0, 0, 0, 0, 1]
            #self.spawn_position(position)
            #rospy.loginfo("Robot stopped at 50 seconds")
            #return
    
        if not self.first_image_received:
            self.first_image_received = True
            self.start_timer()
        if self.elapsed_time < 1.0:
            return
        
        try:
            # Convert image (keeping original mono conversion for line following)
            cv_image_mono = self.bridge.imgmsg_to_cv2(data, "mono8")
        
            # Also get color version for clue processing
            cv_image_color = self.bridge.imgmsg_to_cv2(data, "bgr8")
        
            # Only process clues at the specified interval
            current_time = rospy.Time.now().to_sec()
            if current_time - self.last_processed_time >= self.processing_interval:
                self.last_processed_time = current_time
            
                # Process the color image for clues
                id, message = self.process_ros_image(cv_image_color)
                if id is not None and id not in self.seen_ids:
                    self.seen_ids.add(id)  # Mark ID as seen
                    self.current_id = id
                    self.current_message = message
                    rospy.loginfo(f"Detected ID: {id}, Message: {message}")
                
                    # Publish to score tracker
                    score_msg = f"{self.team_name},{self.password},{id},{message}"
                    self.score_pub.publish(score_msg)
                    
        
            # Continue with existing line following logic
            err = 5
            self.publish_velocity(err)
        
        except CvBridgeError as e:
            rospy.logerr("CvBridge Error: %s", e)


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
        if self.elapsed_time > 1.0 and self.elapsed_time < 10.0:
            rospy.sleep(0.2)
            vel_msg = Twist()
            vel_msg.linear.x = 0.2  # Constant forward speed
            vel_msg.angular.z = 0  # Proportional control for steering
            self.vel_pub.publish(vel_msg)
        if self.elapsed_time > 10.0 and self.elapsed_time < 13.5:
            vel_msg = Twist()
            vel_msg.linear.x = 2
            vel_msg.angular.z = 0
            self.vel_pub.publish(vel_msg)
        if self.elapsed_time > 13.5 and self.elapsed_time < 14:
            vel_msg = Twist()
            vel_msg.linear.x = 0
            vel_msg.angular.z = -3
            self.vel_pub.publish(vel_msg)
        if self.elapsed_time > 14 and self.elapsed_time < 19:
            vel_msg = Twist()
            vel_msg.linear.x = 0.2
            vel_msg.angular.z = 0
            self.vel_pub.publish(vel_msg)
        if self.elapsed_time > 19 and self.elapsed_time < 21:
            vel_msg = Twist()
            vel_msg.linear.x = 0
            vel_msg.angular.z = 0
            self.vel_pub.publish(vel_msg)
            if self.port1 == False:
                self.port1 = True
                position = [0.5, 0, 0.3, 0, 0, 1, 1]
                self.spawn_position(position)
        if self.elapsed_time > 21 and self.elapsed_time < 38:
            vel_msg = Twist()
            vel_msg.linear.x = -0.2
            vel_msg.angular.z = 0
            self.vel_pub.publish(vel_msg)
        if self.elapsed_time > 38 and self.elapsed_time < 42.5:
            vel_msg = Twist()
            vel_msg.linear.x = 2
            vel_msg.angular.z = 0
            self.vel_pub.publish(vel_msg)
        if self.elapsed_time > 42.5 and self.elapsed_time < 44.8:
            vel_msg = Twist()
            vel_msg.linear.x = 0
            vel_msg.angular.z = -3
            self.vel_pub.publish(vel_msg)
        if self.elapsed_time > 44.8 and self.elapsed_time < 49:
            vel_msg = Twist()
            vel_msg.linear.x = 0.2
            vel_msg.angular.z = 0
            self.vel_pub.publish(vel_msg)
        if self.elapsed_time > 49 and self.elapsed_time < 55.4:
            vel_msg = Twist()
            vel_msg.linear.x = 0
            vel_msg.angular.z = 0
            self.vel_pub.publish(vel_msg)
            rospy.sleep(2)
            # Publish a message to /score_tracker to stop the competition timer
            if self.stopped == False:
                self.stopped = True
                stop_msg = f"{self.team_name},{self.password},-1,NA"
                self.score_pub.publish(stop_msg)
                rospy.loginfo("Published stop message to /score_tracker: %s", stop_msg)
            
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