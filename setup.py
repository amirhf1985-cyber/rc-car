setup_content = '''from setuptools import setup, find_packages

setup(
    name="blerc",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        "kivy>=2.2.1",
    ],
    author="AmirHF",
    author_email="your.email@example.com",
    description="BLE RC Car",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: Android",
    ],
    python_requires=">=3.7",
)
'''

with open('setup.py', 'w') as f:
    f.write(setup_content)

print("setup.py is created")