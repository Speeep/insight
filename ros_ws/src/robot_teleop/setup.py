from setuptools import find_packages, setup
import os
from glob import glob

package_name = 'robot_teleop'

setup(
    name=package_name,
    version='0.1.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'launch'), glob('launch/*.py')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='giovanni',
    maintainer_email='speeeep@gmail.com',
    description='This package is for sending twist messages to /cmd_vel to control my robot with keyboard',
    license='Apache-2.0',
    entry_points={
        'console_scripts': [
            'wasdqe_teleop = robot_teleop.wasdqe_teleop:main',
            'image_viewer = robot_teleop.image_viewer:main',
        ],
    },
)
