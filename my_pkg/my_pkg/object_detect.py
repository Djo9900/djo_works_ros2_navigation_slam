import rclpy
import cv2 as cv
from rclpy.node import Node
from sensor_msgs.msg import Image, LaserScan, NavSatFix

from std_msgs.msg import String
from std_msgs.msg import Bool
from my_interfaces.msg import Detect
import math 
import os


from cv_bridge import CvBridge

class ObjectDetect(Node):
    def __init__(self):
        super().__init__('object_detect')

        self.get_logger().info("Node started")

        #### Création du subscriber pour s'abonner au topic LaserScan ####
        self.subscription_laser = self.create_subscription(
            LaserScan,
            "/scan",
            self.laser_callback,  # Remarque : On passe la référence à la fonction sans parenthèses
            10
        )
        
        #### Création du subscriber pour s'abonner au topic Image ####
        self.subscription_image = self.create_subscription(
            Image,
            "/camera/image_raw",
            self.image_callback,
            10
        )
        
        ### subscriber au  NavsatFix pour recupéré la lati, longi et altitude ####*
        
        self.subscription_navsat= self.create_subscription(NavSatFix, "/navsat" ,self.navsat_callback,10)
        
        self.subscription_navsat
        

        ### Création du publisher pour envoyer les messages de détection ####
        self.pub = self.create_publisher(Detect, "detection", 10)

        self.pub

        # ### publiser la distance et l'angle de l'objet détecté ###
        # self.pub_distance_angle = self.create_publisher(Detect, "distance_angle", 10)
        
        # #### Création d'un timer pour publier tous les 5 secondes ####
        self.timer_period_sec = 1200.0  # en secondes
        self.timer = self.create_timer(self.timer_period_sec, self.time_callback)

        #### Instanciation du pont entre ROS et OpenCV ####
        self.bridge = CvBridge()

        #### Initialisation de l'objet message pour la détection ####
        self.detect_msg = Detect()

        self.detect_msg.zone = ""

        self.detect_msg.object_detect = False
        self.detect_msg.angle = 0.0 # en dégrée
        self.detect_msg.distance = 0.0
        

    ### Callback du LaserScan pour détecter les objets ###
    def laser_callback(self, msg: LaserScan):
        self.get_logger().info("Laser callback ok")

        long = len(msg.ranges)
        
        

        # Vérification de la présence d'un objet dans chaque zone
        for i in range(long):
            distance = msg.ranges[i]
            
            
            # Ignorer les valeurs infinies ou invalides
            if math.isinf(distance) or math.isnan(distance):
                continue

            # Zone de droite
            if 0 < i < long // 3:
                if distance <= 5.0:
                    self.detect_msg.zone = "droite"
                    self.detect_msg.object_detect = True
                    self.detect_msg.distance = distance
                    ## calcule de la distnce et l'orientation de l'objet detecté ##
                    self.detect_msg.angle = math.degrees(msg.angle_min + i * msg.angle_increment)
                    

            # Zone du milieu
            elif  long // 3 < i < 2 * long // 3:
                if distance <= 5.0:
                    self.detect_msg.zone = "milieu"
                    self.detect_msg.object_detect = True
                    ## calcule de la distnce et l'orientation de l'objet detecté ##
                    self.detect_msg.angle = math.degrees(msg.angle_min + i * msg.angle_increment)
                   
                    

            # Zone de gauche
            elif 2 * long // 3 < i < long:
                if distance <= 5.0:
                    self.detect_msg.zone = "gauche"
                    self.detect_msg.object_detect = True
                    self.detect_msg.distance = distance
                    ## calcule de la distnce et l'orientation de l'objet detecté ##
                    self.detect_msg.angle = math.degrees(msg.angle_min + i * msg.angle_increment)
                    
        if not self.detect_msg.object_detect:
            self.get_logger().info("Aucun object detetecter")
                
            self.detect_msg.zone = "gauche"
            self.detect_msg.object_detect = False
            self.detect_msg.distance = 0.0
                    ## calcule de la distnce et l'orientation de l'objet detecté ##
            self.detect_msg.angle = 0.0
            

        # # Publier le message de détection
        # self.pub.publish(self.detect_msg)
                 

        # self.get_logger().info(
        #                     f"Zone: {self.detect_msg.zone}"
        #                     f"Object detected: {self.detect_msg.object_detect}"
        #                     f"Distance : {self.detect_msg.distance}"
        #                     f"Angle : {self.detect_msg.angle}"
        # )
            
                                    
    
    # Publication du message de détection ####
    def time_callback(self):
        self.get_logger().info("Time callback ok")
        self.pub.publish(self.detect_msg)
                

    ### Callback pour la capture des images ###
    # def image_callback(self, msg: Image):
    #     ### on execute le code de capture d'image
    #     try:
    #         cv_image = self.bridge.imgmsg_to_cv2(msg, "bgr8")

    #         if self.detect_msg.object_detect:
    #             # Affichage texte sur image
    #             cv.putText(cv_image, f"Objet détecté: {self.detect_msg.zone}, Distance: {self.detect_msg.distance}",
    #                        (50, 50), cv.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)

    #             # Création du dossier si nécessaire
    #             save_dir = "/home/djo9800/image"
    #             os.makedirs(save_dir, exist_ok=True)  # crée le dossier s'il n'existe pas

    #             # Chemin complet du fichier
    #             path = os.path.join(save_dir, "Object_detect.jpg")

    #             # Sauvegarde l'image
    #             cv.imwrite(path, cv_image)
    #             self.get_logger().info(f"Image sauvegardée : {path}")

    #         # Affichage live de la caméra
    #         cv.imshow("Camera", cv_image)
    #         cv.waitKey(10)

    #     except Exception as e:
    #         self.get_logger().error(f"Erreur image_callback : {e}")
    
    
    def image_callback(self, msg: Image):
        try:
            # Conversion de l'imge ros vesr opencv
            cv_image = self.bridge.imgmsg_to_cv2(msg, "bgr8")

            if self.detect_msg.object_detect:
                # Liste des lignes à afficher
                lines = [
                    f"Objet_ detect a : {self.detect_msg.zone}",
                    f"Distance : {self.detect_msg.distance:.2f} m",
                    f"Angle : {self.detect_msg.angle:.1f} deg",
                    f"Longitude : {self.detect_msg.longitude:.6f}",
                    f"Latitude : {self.detect_msg.latitude:.6f}",
                    f"Altitude : {self.detect_msg.altitude:.2f} m"
                ]

                # Position initiale
                x, y0 = 50, 50
                dy = 30  # distance entre les lignes en pixels

                # Affichage ligne par ligne
                for i, line in enumerate(lines):
                    y = y0 + i*dy
                    cv.putText(cv_image, line, (x, y), cv.FONT_HERSHEY_SIMPLEX, 1, (0,0,255), 2)

                # Créer le dossier si inexistant
                save_dir = os.path.expanduser("~/image")
                if not os.path.exists(save_dir):
                    os.makedirs(save_dir)

                # Nom du fichier dynamique
                filename = f"Object_{self.detect_msg.zone}_dist{self.detect_msg.distance:.2f}_angle{self.detect_msg.angle:.1f}.jpg"
                path = os.path.join(save_dir, filename)

                # Sauvegarde de l'image
                cv.imwrite(path, cv_image)
                self.get_logger().info(f"Image sauvegardée : {path}")

            # Affichage live
            cv.imshow("Camera", cv_image)
            cv.waitKey(10)

        except Exception as e:
            self.get_logger().error(f"Erreur image_callback : {e}")

            
    ### Recupération des information sur le Navsat
    
    def navsat_callback(self, msg: NavSatFix):
        
        self.get_logger().info("recuperation des donnéen du GPS")
        
        self.detect_msg.longitude = msg.longitude
        self.detect_msg.latitude = msg.latitude
        self.detect_msg.altitude = msg.altitude
        
        self.get_logger().info(f"Longitude: {self.detect_msg.longitude},"
                               f"Latitude : {self.detect_msg.latitude},"
                               f"Altitude: {self.detect_msg.altitude}")
        


def main(args=None):
    rclpy.init(args=args)

    node = ObjectDetect()  # Instance du nœud
    try:
        rclpy.spin(node)  # Le nœud reste actif jusqu'à interruption
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
