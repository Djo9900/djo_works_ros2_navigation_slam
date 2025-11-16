from setuptools import find_packages, setup
import os
from glob import glob

package_name = 'my_pkg'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        ('share/' + package_name + '/launch', glob('launch/*.launch.py')),
        ('share/' + package_name + '/description', glob('description/*.urdf.xacro')),
        ('share/' + package_name + '/description', glob('description/*.xacro')),
        ('share/' + package_name + '/configuration', glob('configuration/*.yaml')),
        ('share/' + package_name + '/worlds', glob('worlds/*.world')),
        ('share/' + package_name + '/worlds', glob('worlds/*.sdf')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Djo',
    maintainer_email='siradjosy1@gmail.com',
    description='TODO: Package description',
    license='Apache-2.0',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [ 'diff_drive_node = my_pkg.diff_drive:main',
                                'ghish_node = my_pkg.ghish_node:main',
                                'object_detect = my_pkg.object_detect:main',
                                
        ],
    },
)


 