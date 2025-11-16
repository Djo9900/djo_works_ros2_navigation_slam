#!/user/bin/env/python3
import rclpy
import math
import asyncio
from rclpy.node import Node 
from rclpy.action import ActionServer, GoalResponse, CancelResponse
from geometry_msgs.msg import Twist, Pose2D
from turtlesim.msg import Pose
from my_interfaces.action import Goto


class MonNoeudAction(Node):
    def __init__(self):
        super().__init__("noeud_action")
        self.get_logger().info("Noeud lancé!!")


        self.publisher_=   self.create_publisher(Twist,'/turtle1/cmd_vel',10)
        
        self.subscription =  self.create_subscription(Pose,'/turtle1/pose', self.pose_callback,10)

        self._action_server = ActionServer(
            self,
            Goto,
            'goto',
            execute_callback=self.execute_callback,
            goal_callback=self.goal_callback,
            cancel_callback=self.cancel_callback
        )

        self.pose = Pose2D()

    def pose_callback(self,msg:Pose):
            self.pose.x = msg.x
            self.pose.y = msg.y
            self.pose.theta = msg.theta
            #self.get_logger().info(f"Pose actuelle: x={self.pose.x}, y={self.pose.y}, theta={self.pose.theta}")
        
    def goal_callback(self, goal_request):
            self.x = goal_request.target.x
            self.y = goal_request.target.y
            self.theta = goal_request.target.theta
            self.get_logger().info(f"Nouveau goal reçu: x={self.x}, y={self.y}, theta={self.theta}")
            return GoalResponse.ACCEPT
        
    def cancel_callback(self, goal_handle):
            self.get_logger().info('Goal annulé!!')
            return CancelResponse.ACCEPT
        
    def execute_callback(self, goal_handle):
            self.get_logger().info('le noeud est démarré!!')

            feedback_msg= Goto.Feedback()
            result= Goto.Result()
            
            target= goal_handle.request.target

            self.get_logger().info(f'Executing goal to: ({target.x}, {target.y})')

            while rclpy.ok():

                #self.get_logger().info("en cours d'exécution...")
                
                dx = target.x - self.pose.x
                dy = target.y - self.pose.y
                distance = math.hypot(dx, dy) #math.sqrt(dx**2 + dy**2)
                angle_to_goal = math.atan2(dy, dx)

                orientation_error = math.atan2(math.sin(angle_to_goal - self.pose.theta),
                               math.cos(angle_to_goal - self.pose.theta))

                

                if distance < 0.1:
                    self.stop_turtle()
                    goal_handle.succeed()
                    result.reached = True
                    result.final_pose = self.pose
                    self.get_logger().info('Goal atteint')
                    return result
                
                msg = Twist()
                msg.linear.x = min(0.2 * distance,0.2)
                msg.angular.z = min(1.0 * orientation_error,1.0)
                #self.publisher_.publish(msg)

                self.publish_velocity(msg.linear.x, msg.angular.z)


                feedback_msg.current_pose = self.pose
                goal_handle.publish_feedback(feedback_msg)


                if goal_handle.is_cancel_requested:
                    goal_handle.canceled()
                    self.get_logger().info('Goal annulé!')
                    result.reached= False
                    result.final_pose= self.pose

                rclpy.spin_once(self)

                
                #await asyncio.sleep(0.1)

    def stop_turtle(self):
        stop_msg = Twist()
        stop_msg.linear.x = 0.0
        stop_msg.angular.z = 0.0
        self.publisher_.publish(stop_msg)

    def publish_velocity(self, linear, angular):
        msg = Twist()
        msg.linear.x = linear
        msg.angular.z = angular
        self.publisher_.publish(msg)

   
def main(args=None):
    rclpy.init(args=args)
    node = MonNoeudAction()
    rclpy.spin(node)


if __name__ == '__main__':
    main()
    