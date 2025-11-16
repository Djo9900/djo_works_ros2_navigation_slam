from launch import LaunchDescription
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import PathJoinSubstitution, TextSubstitution
import os
import xacro
import launch


def generate_launch_description():

    pkg_path = get_package_share_directory('my_pkg')
    xacro_file = os.path.join(pkg_path, 'description', 'robot.urdf.xacro')
    robot_desc = xacro.process_file(xacro_file).toxml()


    pkg_gazebo = get_package_share_directory('ros_gz_sim')

    gz_sim = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_gazebo, "launch", "gz_sim.launch.py")
        ),
        launch_arguments={
            "gz_args": PathJoinSubstitution([pkg_path, "worlds", "world.sdf"]),
                    
        }.items(),
    )

    # === Retourne la description du lancement ===
    return LaunchDescription([
        # Publie la description du robot dans /robot_description
        Node(
            package='robot_state_publisher',
            executable='robot_state_publisher',
            name='robot_state_publisher',
            output='screen',
            parameters=[{'robot_description': robot_desc}]
        ),

        # Interface graphique pour les articulations (utile pour tests)
        Node(
            package='joint_state_publisher_gui',
            executable='joint_state_publisher_gui',
            name='joint_state_publisher_gui'
        ),

        # Lancement de RViz
        Node(
            package='rviz2',
            executable='rviz2',
            name='rviz2',
            output='screen'
        ),
        
        
         ####" obot_localization_node  pour la fussion des capteur 
        Node(
            package='robot_localization',
            executable='ekf_node',
            name='ekf_node',
            output='screen',
            parameters=[os.path.join(pkg_path, 'config/ekf.yaml')]
        ),

        # Pont entre ROS 2 et Gazebo (communication topics)
        Node(
            package='ros_gz_bridge',
            executable='parameter_bridge',
            parameters=[{
                'config_file': os.path.join(pkg_path, 'configuration', 'bridge.yaml'),
                'qos_overrides./tf_static.publisher.durability': 'transient_local',
            }],
            output='screen'
        ),

        # Création du robot dans Gazebo à partir du topic /robot_description
        Node(
            package='ros_gz_sim',
            executable='create',
            output='screen',
            arguments=[
                '-topic', '/robot_description',
                '-name', 'bot',
                '-allow_renaming', 'true',
                '-x', '0.0',
                '-y', '0.0',
                '-z', '0.1',
                '-R', '0.0',
                '-P', '0.0',
                '-Y', '0.0'
            ],
        ),

        # Lancement de la simulation Gazebo
        gz_sim,
        
        launch.actions.DeclareLaunchArgument(name='use_sim_time', default_value='True',
                                            description='Flag to enable use_sim_time'),
    ])
