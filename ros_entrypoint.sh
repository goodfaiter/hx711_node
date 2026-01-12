#!/bin/bash
set -e

id -u ros &>/dev/null || adduser --quiet --disabled-password --gecos '' --uid ${UID:=1000} ros

if ! getent group gpio > /dev/null; then
    groupadd -g ${GPIO_GROUP_ID:=986} gpio
    echo "Created gpio group"
fi
usermod -aG dialout,gpio ros

source /opt/ros/${ROS_DISTRO}/setup.bash
source /colcon_ws/install/setup.bash || true

exec "$@"