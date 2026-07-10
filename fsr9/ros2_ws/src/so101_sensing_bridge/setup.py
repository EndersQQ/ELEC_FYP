from setuptools import setup

package_name = "so101_sensing_bridge"

setup(
    name=package_name,
    version="0.1.0",
    packages=[package_name, "so101_sensing"],
    package_dir={"so101_sensing": "../../../host/so101_sensing"},
    data_files=[
        ("share/ament_index/resource_index/packages", [f"resource/{package_name}"]),
        (f"share/{package_name}", ["package.xml"]),
    ],
    install_requires=["setuptools", "pyserial"],
    zip_safe=True,
    maintainer="enders",
    maintainer_email="enders@example.com",
    description="Serial bridge for SO-101 gripper FSR/IMU frames.",
    license="MIT",
    entry_points={
        "console_scripts": [
            "fsr_imu_bridge = so101_sensing_bridge.fsr_imu_bridge:main",
        ],
    },
)
