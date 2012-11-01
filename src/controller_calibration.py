#!/usr/bin/env python
"""The Calibration Controller"""
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

import numpy as np

#
# INTERNAL DEPENDENCIES
#

import src.model_calibration as model_calibration
import src.view_calibration as view_calibration
import src.controller_generic as controller_generic
import src.resource_fixture_image as resource_fixture_image

#
# EXCEPTIONS
#

class Bad_Stage_Call(Exception): pass
class No_View_Loaded(Exception): pass
class Not_Yet_Implemented(Exception): pass
class Impossible_Fixture(Exception): pass
class UnDocumented_Error(Exception): pass

#
# CLASSES
#

class Calibration_Controller(controller_generic.Controller):

    def __init__(self, window, main_controller):

        super(Calibration_Controller, self).__init__(window, main_controller)

        self._specific_controller = None

    def _get_default_view(self):

        return view_calibration.Calibration_View(self, self._model)

    def _get_default_model(self):

        return model_calibration.model

    def set_mode(self, widget, calibration_mode):

        view = self._view
        model = self._model

        if calibration_mode == 'fixture':

            self._specific_controller = Fixture_Controller(self._window,
                self, model=model, view=view)

        elif calibration_mode == "poly":

            err = Not_Yet_Implemented("Mode 'Cell Count Calibration'")

            raise err

        else:

            raise Bad_Stage_Call(calibration_mode)

class Fixture_Controller(controller_generic.Controller):

    def __init__(self, window, parent, view=None, model=None,
        specific_model=None):

        super(Fixture_Controller, self).__init__(window, parent,
            view=view, model=model)

        #MODEL
        if specific_model is not None:
            self._specific_model = specific_model
        else:
            self.build_new_specific_model()

        #VIEW
        view.set_controller(self)
        self.set_view_stage(None, 'fixture-select')

    def set_view_stage(self, widget, stage_call, *args, **kwargs):

        if len(args) > 0:
            sm = args[0]
        else:
            sm = self._specific_model

        m = self._model
        view = self._view

        if stage_call == 'fixture-select':

            top = view_calibration.Fixture_Select_Top(self,
                m, sm)
            stage = view_calibration.Fixture_Select_Stage(self,
                m, sm)

        elif stage_call == 'marker-calibration':

            self.set_unsaved()
            self.get_top_controller().fixtures.fill_model(sm)

            top = view_calibration.Fixture_Marker_Calibration_Top(self,
                m, sm)

            if len(sm['marker-positions']) >= 3:
                top.set_allow_next(True)

            stage = view_calibration.Fixture_Marker_Calibration_Stage(self,
                m, sm)

        elif stage_call == 'segmentation':

            top = view_calibration.Fixture_Segmentation_Top(self, 
                m, sm)

            stage = view_calibration.Fixture_Segmentation_Stage(self,
                m, sm)

        elif stage_call == 'save':

            top = view_calibration.Fixture_Save_Top(self, m, sm)
 
            stage = view_calibration.Fixture_Save_Stage(self, m , sm)

            self.save_fixture()

        else:

            err = Bad_Stage_Call("{0} recieved call '{1}' from {2}".format(
                self, stage_call, widget))

            raise err

        view.set_top(top)
        view.set_stage(stage)

    def build_new_specific_model(self):

        sm = model_calibration.copy_model(
            model_calibration.specific_fixture_model)
        self._specific_model = sm
        return sm

    def check_fixture_select(self, widget, is_new):

        stage = self._view.get_stage()
        top = self._view.get_top()
        sm = self._specific_model

        if is_new:

            new_name = stage.new_name.get_text()
            if new_name == "" or new_name in \
                    self.get_top_controller().fixtures.names():

                warn = True
                allow_next = False

            else:

                warn = False
                allow_next = True

            sm['fixture'] = new_name
            sm['new_fixture'] = True

        else:

            treemodel, rows = stage.selection.get_selected_rows()
            allow_next = len(rows) > 0
            warn = None
            if allow_next:
                sm['fixture'] = treemodel[rows[0]][0]
            sm['new_fixture'] = False


        stage.set_bad_name_warning(warn)
        top.set_allow_next(allow_next)

    def set_image_path(self, widget):

        image_list = view_calibration.select_file(
            self._model['fixture-image-dialog'],
            multiple_files=False,
            file_filter=self._model['fixture-image-file-filter'])

        if len(image_list) > 0:

            self._specific_model['im-path'] = image_list[0]
            self._specific_model['marker-positions'] = list()
            self._specific_model['im-scale'] = 1.0
            self._view.get_stage().set_new_image()

            self._view.get_stage().check_allow_marker_detection()

    def handle_keypress(self, widget, event):

        sm = self._specific_model

        if sm['active-segment'] is not None:

            if view_calibration.gtk.gdk.keyval_name(event.keyval) == "Delete":

                if sm['active-segment'] == 'G':

                    sm['grayscale-coords'] = list()
                    sm['grayscale-sources'] = None

                else:

                    try:
                        plate = int(sm['active-segment'][-1]) - 1
                    except:
                        plate = None

                    if plate is not None:
                        sm['plate-coords'][plate] = None

            self._view.get_stage().update_segment(sm['active-segment'],
                scale=sm['im-original-scale'])

    def save_fixture(self):

        sm = self._specific_model
        self.f_settings.reset_all_pinning_histories()

        for plate in enumerate(sm['plate-coords']):
            self.f_settings['plate-coords'] = plate

        self.f_settings['grayscale'] = sm['grayscale-targets']
        self.f_settings.reset_all_pinning_histories()
        self.f_settings['current'].save()
        self.get_top_controller().fixtures.update()

    def set_number_of_markers(self, widget):

        s = widget.get_text()

        if s != "":

            try:

                n = int(widget.get_text())

            except:

                n = 0
                widget.set_text(str(n))

        else:

            n = 0

        self._specific_model['markers'] = n
        self._view.get_stage().check_allow_marker_detection()

    def run_marker_detect(self, widget):

        sm = self._specific_model

        if sm['markers'] >= 3 and sm['im'] is not None:

            if sm['marker-path'] is None:
                sm['marker-path'] = self.get_top_controller().paths.marker

            self.f_settings = resource_fixture_image.Fixture_Image(
                sm['fixture-file'],
                fixture_directory=self.get_top_controller().paths.fixtures, 
                image_path=sm['im-path'],
                im_scale=(sm['im-scale']<1 and sm['im-scale'] or None),
                define_reference=True, markings_path=sm['marker-path'],
                markings=sm['markers'])

            self.f_settings.run_marker_analysis()
            X, Y = self.f_settings['markers']

            if X is not None and Y is not None:

                sm['marker-positions'] = zip(X, Y)

            else:
   
                sm['marker-positions'] = None

            self._view.get_stage().set_markers()

            if len(sm['marker-positions']) >= 3:
                self._view.get_top().set_allow_next(True)

        else:

            err = Impossible_Fixture(
                "Markers must be at least 3 (you have '{0}')".format(
                sm['markers']) + " and you need an image too")

            raise err

        if len(sm['marker-positions']) > 3:
            top.set_allow_next(True)

    def toggle_grayscale(self, widget):

        has_gs = widget.get_active()
        stage = self._view.get_stage()
        sm = self._specific_model
        sm['grayscale-exists'] = has_gs
        if has_gs == False:
            sm['grayscale-coords'] = list()
            sm['grayscale-sources'] = None
            stage.update_segment('G',
                scale=sm['im-original-scale'])
        
        stage.set_segments_in_list()
        

    def set_number_of_plates(self, widget):

        try:
            plates = int(widget.get_text())
        except:
            plates = 0
            if widget.get_text() != "":
                widget.set_text("{0}".format(plates))

        sm = self._specific_model

        stage = self._view.get_stage()
        old_number_of_plates = len(sm['plate-coords'])
        for p in xrange(plates, old_number_of_plates):
            sm['plate-coords'][p] = None
            stage.update_segment("P{0}".format(p + 1))
        sm['plate-coords'] += [None] * (plates - len(sm['plate-coords']))
        sm['plate-coords'] = sm['plate-coords'][:plates]

        self._view.get_stage().set_segments_in_list()

    def set_active_segment(self, selection):

        store, rows = selection.get_selected_rows()
        sm = self._specific_model

        if len(rows) == 0:

            sm['active-segment'] = None

        else:

            row = rows[0]
            sm['active-segment'] = store[row][2]

    def set_allow_save(self, val):

        if val and len(self._specific_model['plate-coords']) > 0:
            self._view.get_top().set_allow_next(True)
        else:
            self._view.get_top().set_allow_next(False)

    def get_segment_ok(self, pos1, pos2):

        if pos1 is None or None in pos1 or pos2 is None or None in pos2:

            return None

        return zip(*map(sorted, zip(*(pos1, pos2))))

    def get_grayscale(self):

        sm = self._specific_model

        if len(sm['grayscale-coords']) != 2:

            gs_ok = False

        else:

            self.f_settings['grayscale-coords'] = sm['grayscale-coords']
 
            self.f_settings.analyse_grayscale()
            gs_target, gs_source =  self.f_settings['grayscale']
            print gs_source
            if gs_source is not None:
                gs_source = np.array(gs_source)

            if gs_source is not None and gs_target is not None and \
                ((sm['grayscale-targets'] - gs_target) == 0).all() and \
                ((gs_source[:-1] - gs_source[1:]) > 0).sum() \
                in (0, len(gs_source) - 1):

                sm['grayscale-sources'] = gs_source
                gs_ok = True

            else:

                gs_ok = False

        if gs_ok == False:

            sm['grayscale-sources'] = None

        return gs_ok

    def mouse_press(self, event, *args, **kwargs):

        sm = self._specific_model
        scale = sm['im-original-scale']

        if sm['active-segment'] is not None:
            if event.xdata is not None and event.ydata is not None:
                sm['active-source'] = (event.xdata / scale,
                    event.ydata / scale)
            else:
                sm['active-source'] = None

    def mouse_release(self, event, *args, **kwargs):

        sm = self._specific_model
        scale = sm['im-original-scale']

        if sm['active-segment'] is not None:
            if event.xdata is not None and event.ydata is not None:

                sm['active-target'] = (event.xdata / scale,
                    event.ydata / scale)
            
            coords = self.get_segment_ok(sm['active-source'],
                sm['active-target'])

            if coords is not None:

                if sm['active-segment'] == "G":

                    sm['grayscale-coords'] = coords
                    self.get_grayscale()

                else:
                    try:

                        plate = int(sm['active-segment'][-1]) - 1
                    except:
                        plate = None

                    if plate is not None:
                        sm['plate-coords'][plate] = coords

                self._view.get_stage().draw_active_segment(
                    scale=scale)

        sm['active-source'] = None
        sm['active-target'] = None

    def mouse_move(self, event, *args, **kwargs):

        sm = self._specific_model
        scale = sm['im-original-scale']

        if sm['active-segment'] is not None and \
                sm['active-source'] is not None:

            if event.xdata is not None and event.ydata is not None:

                sm['active-target'] = (event.xdata / scale,
                    event.ydata / scale)
 
            self._view.get_stage().draw_active_segment(scale=scale)