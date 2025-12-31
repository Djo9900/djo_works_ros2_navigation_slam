import os
import launch
from launch  import LaunchDescription
from launch_ros.actions import Node
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration

from ament_index_python import get_package_share_directory


def generate_launch_description():
    
    
    #### definir le chemin du package slam et celui de la configuration des parametre
    package_slam = get_package_share_directory('robot_slam')
    
    slam_param_path = os.path.join(package_slam, "config", "slam_toolbox.yaml")
    
    #### definition des launchs configuration
    
    use_sim_time = LaunchConfiguration("use_sim_time")
    params_file = LaunchConfiguration("params_file")
    
    
    return LaunchDescription(
        [
            DeclareLaunchArgument(
                "use_sim_time",
                default_value = "true",
                description = "Flag to enable use_sim_time"                
            ),
            
            DeclareLaunchArgument(
                "params_file",
                default_value= slam_param_path,
                description="Full path to the ROS2 parameters file to use for the slam_toolbox node"
            ),
            Node(
                package='slam_toolbox',
                executable='async_slam_toolbox_node',
                name='slam_toolbox',
                output='screen',
                parameters=[params_file, {'use_sim_time': use_sim_time}],
            )
        ]
    )
    
    
    
    