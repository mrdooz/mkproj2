# yapp - yet another project generator

# +-------------------+
# | platform          |
# | libs              |
# +-------------------+
# +-------------------+
# | |dir|  generate   |
# | status            |
# +-------------------+


# cmake_minimum_required(VERSION 3.5)

# project(MyProject)

# # Add all C files in the src directory to the project
# file(GLOB SOURCES "src/*.c")

# # Create the executable
# add_executable(MyExecutable ${SOURCES})

# MSVC project guids: Windows (Visual C++)   {8BC9CEB8-8B4A-11D0-8D11-00A0C91BC942}

import sys
import os
from PySide6 import QtCore, QtGui
from PySide6.QtWidgets import *
import uuid
import random
import shutil
import zipfile

from jinja2 import Environment, FileSystemLoader

JOIN = os.path.join

def generate_project(project_name, dest_dir : str, platform, libs):

    dest_dir = dest_dir.replace('\\', '/')

    # Either create the destination directory, or make sure it's empty
    if os.path.exists(dest_dir) and os.path.isdir(dest_dir):
        if len(os.listdir(dest_dir)) > 0:
            raise RuntimeError('Destination directory must be empty')
    else:
        os.makedirs(dest_dir)

    script_dir = os.path.dirname(os.path.realpath(__file__))
    # src_dir = JOIN(script_dir, 'src/')
    package_dir = JOIN(script_dir, 'packages/')

    project_dir = JOIN(dest_dir, '_win32')
    contrib_dir = JOIN(dest_dir, 'contrib/')
    # raylib_dir = JOIN(contrib_dir, 'raylib')
    os.makedirs(project_dir)

    with_raylib = 'raylib' in libs
    with_raylib_gui = 'raylibgui' in libs
    with_livepp = 'live++' in libs
            
    environment = Environment(loader=FileSystemLoader(JOIN(script_dir,"templates/msvc2022")))

    def apply_template(template_filename, template_dict, dest_path):
        template = environment.get_template(template_filename)
        content = template.render(template_dict)
        with open(dest_path, 'wt', encoding="utf-8") as f:
            f.write(str(content))

    template_dict = {
        'project_name':project_name,
        'project_guid':str(uuid.uuid4()).upper(),
        'src_dir':dest_dir,
        'sources_files_guid':str(uuid.uuid4()).upper(),
        'header_files_guid':str(uuid.uuid4()).upper(),
        'resource_files_guid':str(uuid.uuid4()).upper(),
        'contrib_guid':str(uuid.uuid4()).upper(),
        'raylib_guid':str(uuid.uuid4()).upper(),
        'raylib_src_guid':str(uuid.uuid4()).upper(),
        'raylib_inc_guid':str(uuid.uuid4()).upper(),
        'with_raylib':with_raylib or with_raylib_gui,
        'with_raylib_gui': with_raylib_gui,
        'with_livepp': with_livepp,
    }

    # Create the solution and project files
    apply_template('minimal_raylib.sln.template', template_dict, JOIN(project_dir, project_name + '.sln'))
    apply_template('minimal_raylib.vcxproj.filters.template', template_dict, JOIN(project_dir, project_name + '.vcxproj.filters'))
    apply_template('minimal_raylib.vcxproj.template', template_dict, JOIN(project_dir, project_name + '.vcxproj'))
    
    # Create the main.cpp
    if with_raylib_gui:
        apply_template('main_raylib_gui.cpp.template', template_dict, JOIN(dest_dir, 'main.cpp'))
    elif with_raylib:
        apply_template('main_raylib.cpp.template', template_dict, JOIN(dest_dir, 'main.cpp'))
    else:
        apply_template('main.cpp.template', template_dict, JOIN(dest_dir, 'main.cpp'))
    
    # Extract the packages
    if len(libs) > 0:
        os.makedirs(contrib_dir)

    if with_raylib or with_raylib_gui:
        with zipfile.ZipFile(JOIN(package_dir, 'raylib.zip')) as zip_ref:
            zip_ref.extractall(contrib_dir)

    if with_livepp:
        with zipfile.ZipFile(JOIN(package_dir, 'livepp.zip')) as zip_ref:
            zip_ref.extractall(contrib_dir)

class MyWidget(QWidget):
    # Note, the GUI elements hold the data, and then when we press the generate button, we
    # pull that data from the GUI, and pass it to generate_project
    def __init__(self):
        super().__init__()
        self.lib_checkboxes = []
        self.edit_path : QLineEdit = None
        self.edit_project_name : QLineEdit = None
        self.edit_status : QLineEdit = None
        self.platform_combo : QComboBox = None

        def create_platform_group():
            # Platform group
            platform_group = QGroupBox("Platform")
            self.platform_combo = QComboBox()
            self.platform_combo.addItems(['Windows', 'OSX'])

            vbox = QVBoxLayout()
            vbox.addWidget(self.platform_combo)
            hbox = QHBoxLayout()

            for lib in ['Raylib', 'RaylibGui', 'Live++', 'Tiled', 'AseSprite']:
                checkbox = QCheckBox(lib)
                self.lib_checkboxes.append(checkbox)
                hbox.addWidget(checkbox)

            vbox.addLayout(hbox)
            platform_group.setLayout(vbox)
            return platform_group

        def create_gen_group():
            # Generate group
            gen_group = QGroupBox("Generate")

            vbox = QVBoxLayout()

            btn_select_directory = QPushButton("...")
            btn_select_directory.clicked.connect(self.on_select_directory)
            btn_generate = QPushButton("Generate")
            btn_generate.clicked.connect(self.on_generate)
            self.edit_path = QLineEdit()
            self.edit_project_name = QLineEdit()
            self.edit_status = QLineEdit()

            def random_project_name():
                # create a default project name
                part1 = ['ornate', 'elaborate', 'decorative', 'extravagant', 'lavish', 'opulent', 'sumptuous', 'plush', 'posh', 'luxurious', 'elegant', 'refined', 'sophisticated', 'chic', 'fashionable', 'stylish', 'fancy-pants', 'swanky', 'flashy', 'showy']
                part2 = ['celebration', 'festivity', 'gala', 'fiesta', 'fete', 'get-together', 'bash', 'shindig', 'soiree', 'reception', 'jamboree', 'banquet', 'ball', 'function', 'event', 'happening', 'meet-up', 'mixer', 'rave']
                project_name = random.choice(part1) + '-' + random.choice(part2)
                self.edit_project_name.setText(project_name)
                self.edit_path.setText(os.path.join(os.getcwd(), project_name))

            random_project_name()
            hbox = QHBoxLayout()
            hbox.addWidget(QLabel("Name"))
            hbox.addWidget(self.edit_project_name)
            btn_random = QPushButton("Random")
            btn_random.clicked.connect(random_project_name)

            hbox.addWidget(btn_random)
            vbox.addLayout(hbox)

            hbox = QHBoxLayout()
            hbox.addWidget(btn_select_directory)
            hbox.addWidget(self.edit_path)
            vbox.addLayout(hbox)
            
            vbox.addWidget(btn_generate)

            hbox = QHBoxLayout()
            hbox.addWidget(QLabel("Status"))
            hbox.addWidget(self.edit_status)
            vbox.addLayout(hbox)

            gen_group.setLayout(vbox)
            return gen_group

        vbox = QVBoxLayout(self)
        vbox.addWidget(create_platform_group())
        vbox.addWidget(create_gen_group())

    @QtCore.Slot()
    def on_select_directory(self):
        self.gen_path = str(QFileDialog.getExistingDirectory(self, "Select Directory"))
        if self.gen_path:
            self.edit_path.setText(self.gen_path)

    @QtCore.Slot()
    def on_generate(self):
        libs = []
        for lib in self.lib_checkboxes:
            if lib.isChecked():
                libs.append(lib.text().lower())
        try:
            self.edit_status.setText('')
            generate_project(self.edit_project_name.text(), self.edit_path.text(), self.platform_combo.currentText(), libs)
            self.edit_status.setText('Success!')
        except Exception as e:
            self.edit_status.setText('Error: {}'.format(str(e)))

if __name__ == "__main__":
    app = QApplication([])

    widget = MyWidget()
    widget.setWindowTitle("MkProj V2.0!!")
    widget.resize(350, 100)
    widget.show()

    sys.exit(app.exec())
