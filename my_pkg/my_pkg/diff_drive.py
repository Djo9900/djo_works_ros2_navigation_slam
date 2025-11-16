#!/usr/bin/env python3
import math
import time

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist, Pose2D

# Importation du service GetPose

from my_interface.srv import GetPose

# Importation de l'action Goto
from rclpy.action import ActionServer, GoalResponse, CancelResponse

from my_interfaces import Goto

class DiffDriveNode(Node):
    
    def __init__(self):
        super().__init__('diff_drive_node')

        self.get_logger().info('DiffDriveNode started')
        
        self.subscription = self.create_subscription(                  # Methode pour souscrire à un topic 
            Twist,                                                     # type de message attendu
            'cmd_vel',                                                 # nom du topic
            self.cmd_vel_callback,                                     # fonction de rappel appelée à chaque message reçu       
            10)                                                        # taille de la file 
        self.subscription                                              # pour éviter un avertissement "variable inutilisée"

        # Publication de la position estimée
        self.publisher = self.create_publisher(                        # Methode pour publier sur un topic
            Pose2D,                                                    # message de pose (x,y,theta)
            'position',                                                # nom du topic
            10)                                                        # taille de la file 
        
        
        timer_period = 1.0  # secondes
        self.timer = self.create_timer(timer_period, self.timer_callback)


        ############### Definition serveur de service #################
        self.srv = self.create_service(GetPose, 'get_pose', self.get_pose_callback)

        ############### Definition serveur d'action #################
        self._action_server = ActionServer(
            self,
            Goto,
            'goto',
            execute_callback=self.execute_callback,
            goal_callback=self.goal_callback,
            cancel_callback=self.cancel_callback
        )

        # Variables d’état du robot (intialisées à zéro)
        self.x = 0.0
        self.y = 0.0
        self.theta = 0.0
        self.last_time = time.time()


    def timer_callback(self):
        """Fonction appelée périodiquement par le timer (toutes les secondes)"""

        # Préparation du message Pose2D
        pose = Pose2D(x=self.x, y=self.y, theta=self.theta)

        self.publisher.publish(pose)  # publication de la pose


    def get_pose_callback(self, request, response):
        """Fonction de rappel pour le service get_pose"""
        response.x = self.x
        response.y = self.y
        response.theta = self.theta
        self.get_logger().info(f'Service get_pose called: ({self.x:.2f}, {self.y:.2f}, {self.theta:.2f})')
        return response
        


    def cmd_vel_callback(self, msg: Twist):
        """Definition de la fonction de rappel pour traiter les messages cmd_vel"""

        current_time = time.time()
        dt = current_time - self.last_time
        
        v = msg.linear.x    # vitesse linéaire
        w = msg.angular.z   # vitesse angulaire

        self.move_rebot(v, w, dt)

        # intégration des équations d’un robot différentiel
        # self.x += v * math.cos(self.theta) * dt    # mise à jour de x
        # self.y += v * math.sin(self.theta) * dt    # mise à jour de y
        # self.theta += w * dt                      # mise à jour de theta

        # Préparation du message Pose2D
        # pose = Pose2D()
        # pose.x = self.x
        # pose.y = self.y
        # pose.theta = self.theta

        # self.publisher.publish(pose)  # publication de la pose

        # Journaux pour le débogage
        
        self.last_time = current_time

    def move_rebot(self, v, w, dt):
        """Met à jour la position du robot en fonction des vitesses linéaire et angulaire."""
        self.x += v * math.cos(self.theta) * dt
        self.y += v * math.sin(self.theta) * dt
        self.theta += w * dt
        # logger pour le débogage
        self.get_logger().info(f'cmd_vel: v={v:.2f}, w={w:.2f} | pose: ({self.x:.2f}, {self.y:.2f}, {self.theta:.2f})')

    ############### Definition des callbacks d'action #################
    def goal_callback(self, goal_request):
        """Accepter ou rejeter une nouvelle demande de but."""
        self.get_logger().info(f'Received goal: {goal_request.target}')
        return GoalResponse.ACCEPT  

    def cancel_callback(self, goal_handle):
        self.get_logger().info('Received cancel request')
        return CancelResponse.ACCEPT

    def execute_callback(self, goal_handle):
        """Boucle d’exécution: diriger le robot vers la cible, publier le feedback, renvoyer le résultat."""
        target = goal_handle.request.target
        feedback_msg = Goto.Feedback()
        
        self.get_logger().info(f'Executing goal to: ({target.x}, {target.y})')
       
        while rclpy.ok():
            # Calcul du vecteur vers la cible
            dx = target.x - self.x
            dy = target.y - self.y
            distance = math.hypot(dx, dy)
            angle_to_goal = math.atan2(dy, dx)
            
            orientation_error = math.atan2(math.sin(angle_to_goal - self.theta),
                               math.cos(angle_to_goal - self.theta))

            # Conditions d’arrêt 
            if distance < 0.05:
                goal_handle.succeed()
                result = Goto.Result()
                result.reached = True
                result.final_pose = Pose2D(x=self.x, y=self.y, theta=self.theta)
                
                return result

            # Commander la vitesse (proportionnelle à la distance et à l’erreur d’orientation)
            v = min(0.5 * distance, 0.5)  
            w = min(2.0 * orientation_error, 1.0)

            self.move_rebot(v, w, 0.1)  # mise à jour de la position

           
            # Publier le feedback
            feedback_msg.current_pose = Pose2D(x=self.x, y=self.y, theta=self.theta)
            goal_handle.publish_feedback(feedback_msg)

            # Vérifier l’annulation
            if goal_handle.is_cancel_requested:
                goal_handle.canceled()
                result = Goto.Result()
                result.reached = False
                result.final_pose = Pose2D(x=self.x, y=self.y, theta=self.theta)
                return result

            


def main(args=None):
    rclpy.init(args=args)
    node = DiffDriveNode() #instance du nœud
    try:
        rclpy.spin(node)  # le nœud reste actif jusqu'à interruption
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
