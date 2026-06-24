from setuptools import setup, find_packages

setup(
    name="library_management",
    version="1.0.0",
    description="Library Management System with Integrated Accounting",
    author="Klaimify Pvt. Ltd.",
    author_email="support@klaimify.in",
    packages=find_packages(),
    zip_safe=False,
    include_package_data=True,
    install_requires=[],  # frappe is provided by the bench environment
)
