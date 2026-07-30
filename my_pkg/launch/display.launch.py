from launch import LaunchDescription
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory
from launch.actions import IncludeLaunchDescription,DeclareLaunchArgument
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import PathJoinSubstitution, TextSubstitution,PythonExpression
from launch.substitutions import LaunchConfiguration
from launch.conditions import IfCondition, UnlessCondition
import os
import xacro
import launch


def generate_launch_description():

    pkg_path = get_package_share_directory('my_pkg')
    xacro_file = os.path.join(pkg_path, 'description', 'robot.urdf.xacro')
    robot_desc = xacro.process_file(xacro_file).toxml()


    pkg_gazebo = get_package_share_directory('ros_gz_sim')
    
    # Déclaration de la variable use_sim_time
    use_sim_time = LaunchConfiguration('use_sim_time', default='true')
    use_ros2_control = LaunchConfiguration('use_ros2_control', default='true')
    
    # use_rviz = LaunchConfiguration("use_rviz").perform(context)

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
        
        DeclareLaunchArgument(
            'use_sim_time',
            default_value='true',
            description='Use simulation (Gazebo) clock if true'
        ),
        
        # Publie la description du robot dans /robot_description
        Node(
            package='robot_state_publisher',
            executable='robot_state_publisher',
            name='robot_state_publisher',
            output='screen',
            parameters=[{'robot_description': robot_desc,
                         'use_sim_time': use_sim_time}]
        ),

        # Interface graphique pour les articulations (utile pour tests)
        Node(
            package='joint_state_publisher',
            executable='joint_state_publisher',
            name='joint_state_publisher',
            parameters=[
            {
                "robot_description": robot_desc,
                "use_sim_time": use_sim_time
            }
        ],
        ),

        # Lancement de RViz
        Node(
            package='rviz2',
            executable='rviz2',
            name='rviz2',
            output='screen',
            parameters=[{'use_sim_time': use_sim_time}]
            
            
        ),
        
        Node(
            package="controller_manager",
            executable="spawner",
            arguments=["joint_broad", "--controller-manager-timeout", "60"],
            #condition=IfCondition(PythonExpression(['"', use_ros2_control, '" == "true"']))
            
        ),
        
        
        Node(
            package="controller_manager",
            executable="spawner",
            arguments=["diff_drive_controller", "--controller-manager-timeout", "60"],
            #condition=IfCondition(PythonExpression(['"', use_ros2_control, '" == "true"'])),
        ),
        
         ####" obot_localization_node  pour la fussion des capteur 
        # Node(
        #     package='robot_localization',
        #     executable='ekf_node',
        #     name='ekf_node',
        #     output='screen',
        #     parameters=[
        #                     os.path.join(pkg_path, 'configuration', 'ekf.yaml'),
        #                     {'use_sim_time': use_sim_time}]
        # ),

        # Pont entre ROS 2 et Gazebo (communication topics)
        Node(
            package='ros_gz_bridge',
            executable='parameter_bridge',
            parameters=[{
                'config_file': os.path.join(pkg_path, 'configuration', 'bridge.yaml'),
                'qos_overrides./tf_static.publisher.durability': 'transient_local',
                'use_sim_time': use_sim_time
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
    ])
