#!/usr/bin/env python
"""The Main Controller"""
__author__ = "Martin Zackrisson"
__copyright__ = "Swedish copyright laws apply"
__credits__ = ["Martin Zackrisson"]
__license__ = "GPL v3.0"
__version__ = "0.997"
__maintainer__ = "Martin Zackrisson"
__email__ = "martin.zackrisson@gu.se"
__status__ = "Development"

#
# DEPENDENCIES
#

import gobject
import os
import gtk

#
# INTERNAL DEPENDENCIES
#

import src.model_main as model_main
import src.view_main as view_main
import src.controller_generic as controller_generic
import src.controller_analysis as controller_analysis
import src.controller_experiment as controller_experiment
import src.controller_calibration as controller_calibration
import src.resource_os as resource_os

#
# EXCEPTIONS
#

class UnknownContent(Exception): pass

#
# CLASSES
#


class Paths(object):

    def __init__(self, program_path, config_file=None):

        self.root = program_path
        self.scanomatic = self.root + os.sep + "run_analysis.py"
        self.src = self.root + os.sep + "src"
        self.analysis = self.src + os.sep + "analysis.py"
        self.config = self.src + os.sep + "config"
        self.fixtures = self.config + os.sep + "fixtures"
        self.images = self.src + os.sep + "images"
        self.marker = self.images + os.sep + "orientation_marker_150dpi.png" 
        self.log = self.src + os.sep + "log"


class Fixture_Settings(object):

    def __init__(self, dir_path, name):

        self.dir_path = dir_path
        self.file_name = name
        self.im_path = dir_path + os.sep + name + ".tiff"
        self.scale = 0.25
        self.name = name.replace("_", " ").capitalize()


class Fixtures(object):

    def __init__(self, paths):

        self._paths = paths
        self._fixtures = None
        self.update()

    def __getitem__(self, fixture):

        if self._fixtures is not None and fixture in self._fixtures:

            return self._fixtures[fixture]

        return None

    def update(self):

        directory = self._paths.fixtures
        extension = ".config"

        list_fixtures = map(lambda x: x.split(extension,1)[0], 
            [file for file in os.listdir(directory) 
            if file.lower().endswith(extension)])

        self._fixtures = dict()

        for f in list_fixtures:
            fixture = Fixture_Settings(directory, f)
            self._fixtures[fixture.name] = fixture

    def names(self):

        if self._fixtures is None:
            return list()

        return self._fixtures.keys()

    def fill_model(self, model):

        fixture=model['fixture']
        if fixture in self._fixtures.keys():

            model['im-original-scale'] = self._fixtures[fixture].scale
            model['im-scale'] = self._fixtures[fixture].scale
            model['im-path'] = self._fixtures[fixture].im_path
            model['fixture-file'] = self._fixtures[fixture].file_name

        else:

            model['im-original-scale'] = 1.0
            model['im-scale'] = 1.0
            model['im-path'] = None
            model['fixture-file'] = model['fixture'].lower().replace(" ","_")


class Scanner(object):

    def __init__(self, paths, config, name):

        self._paths = paths
        self._config = config
        self._name = name
        self._claimed = False
        self._master_process = None

    def _write_to_lock_file(self):

        pass

    def get_claimed(self):

        return self._claimed

    def get_name(self):

        return self._name

    def set_claimed(self, val, master_proc=None):

        self._claimed = val
        if val == True and master_proc is not None:
            self._master_process = master_proc
        
        self._write_to_lock_file()


class Scanners(object):

    def __init__(self, paths, config):

        self._paths = paths
        self._config = config
        self._scanners = dict()
        self._generic_naming = True

    def update(self):

        scanner_count = self._config.number_of_scanners
        if self._generic_naming:
            scanner_name_pattern = "Scanner {0}"
            scanners = [scanner_name_pattern.format(s + 1) for s in xrange(scanner_count)]
        else:
            scanners = self._config.scanner_names

        for s in scanners:

            if s not in self._scanners.keys():
                self._scanners[s] = Scanner(self._paths, self._config, s)

        for s in self._scanners.keys():

            if s not in scanners:

                del self._scanners[s]

    def names(self, available=True):

        self.update()

        scanners = [s_name for s_name, s in self._scanners.items() if available and \
            (s.get_claimed() == False) or True]

        return sorted(scanners)


class Config(object):

    def __init__(self, paths):

        self._paths = paths

        #TMP SOLUTION TO BIGGER PROBLEMS
        self.number_of_scanners = 3
        self.scanner_names = list()

class Controller(controller_generic.Controller):

    def __init__(self, model, view, program_path):

        super(Controller, self).__init__(view, None)

        self.paths = Paths(program_path)
        self.fixtures = Fixtures(self.paths)
        self.config = Config(self.paths)
        self.scanners = Scanners(self.paths, self.config)

        self._model = model
        self._view = view
        self._subprocesses = list()
        gobject.timeout_add(1000, self._subprocess_callback)

        if view is not None:
            view.set_controller(self)

    def add_subprocess(self, proc, stdin=None, stdout=None, stderr=None,
                        pid=None, proc_name=None):

        self._subprocesses.append((proc, pid, stdin, stdout, stderr, proc_name))

    def get_subprocesses(self, by_name=None):

        ret = [p for p in self._subprocesses 
                if (by_name is not None and p[-1] == by_name or True)]

        return ret

    def _subprocess_callback(self):

        return True

    def add_contents(self, widget, content_name):

        m = self._model
        if content_name in ('analysis', 'experiment', 'calibration'):
            title = m['content-page-title-{0}'.format(content_name)]

        if content_name == 'analysis':
            c = controller_analysis.Analysis_Controller(self._view, self)
        elif content_name == 'experiment':
            c = controller_experiment.Experiment_Controller(self._view, self)
        elif content_name == 'calibration':
            c = controller_calibration.Calibration_Controller(self._view, self)
        else:
            err = UnknownContent("{0}".format(content_name))
            raise err

        page = c.get_view()
        self._view.add_notebook_page(page, title, c)
        self.add_subcontroller(c)

    def remove_contents(self, widget, page_controller):

        view = self._view
        if page_controller.ask_destroy():
            view.remove_notebook_page(page_controller.get_view())
            for i, c in enumerate(self._controllers):
                if c == page_controller:
                    del self._controllers[i]
                    break

    def ask_quit(self, *args):

        #INTERIM SOLUTION, SHOULD HANDLE SUBPROCS
        if self.ask_destroy():

            gtk.main_quit()