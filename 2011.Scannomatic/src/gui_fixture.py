#!/usr/bin/env python
"""GTK-GUI for setting up a fixture"""

__author__ = "Martin Zackrisson"
__copyright__ = "Swedish copyright laws apply"
__credits__ = ["Martin Zackrisson"]
__license__ = "GPL v3.0"
__version__ = "0.992"
__maintainer__ = "Martin Zackrisson"
__email__ = "martin.zackrisson@gu.se"
__status__ = "Development"

#
# DEPENDENCIES
#

#from PIL import Image, ImageWin

import pygtk
pygtk.require('2.0')

import gtk, pango
import os, os.path, sys
import types

import matplotlib.image as plt_img
import matplotlib.pyplot as plt
import matplotlib.text as plt_text
import matplotlib.patches as plt_patches
from matplotlib.backends.backend_gtk import FigureCanvasGTK as FigureCanvas
import numpy as np

#
# SCANNOMATIC LIBRARIES
#

import src.resource_fixture as fixture_settings
import src.gui_grayscale as grayscale
#
# CLASSES
#

class Fixture_GUI(gtk.Frame):

    def __init__(self, owner):

        gtk.Frame.__init__(self, "CONFIGURATION OF FIXTURES")

        self.owner = owner
        self.DMS = self.owner.DMS

        #configuring a fixture
        self.current_fixture_settings = []
        self._fixture_gui_updating = False
        self.fixture_active_pos = None
        self.fixture_active_pos_setting = None

        self._fixture_config_root = self.owner._program_config_root + os.sep + "fixtures"
        self.f_settings = fixture_settings.Fixture_Settings(self._fixture_config_root, fixture="fixture_a")
        analysis_img = self._fixture_config_root + os.sep + self.f_settings.fixture_name + ".tiff"

        vbox2 = gtk.VBox(False, 0)
        vbox2.show()
        self.add(vbox2)

        hbox = gtk.HBox()
        hbox.show()
        vbox2.pack_start(hbox, False, False, 0)

        if os.path.isfile(analysis_img):
            self.fixture_analysis_image = plt_img.imread(analysis_img)

        self.scale_factor = 2.0

        image_size = (self.fixture_analysis_image.shape[0]/self.scale_factor,
            self.fixture_analysis_image.shape[1]/self.scale_factor)

        self.plot_selecting = False
        self.plot_ul  = (0,0)

        self.DMS("Fixture init","Setting up figure display",100)
        self.image_fig = plt.Figure(figsize=image_size, dpi=150)
        image_plot = self.image_fig.add_subplot(111)
        image_canvas = FigureCanvas(self.image_fig)

        self.DMS("Fixture init","Figure: Connetcting events",100)
        self.image_fig.canvas.mpl_connect('button_press_event', self.plot_click)
        self.image_fig.canvas.mpl_connect('button_release_event', self.plot_release)
        self.image_fig.canvas.mpl_connect('motion_notify_event', self.plot_move)

        self.DMS("Fixture init","Figure: Plotting image",100)
        image_ax = image_plot.imshow(self.fixture_analysis_image, cmap=plt.cm.gray)

        self.DMS("Fixture init","Figure: Initialising selection rectangle",100)
        self.selection_rect = plt_patches.Rectangle(
                (0,0),0,0, ec = 'k', fill=False, lw=0.2
                )
        self.selection_rect.get_axes()
        self.selection_rect.get_transform()
        image_plot.add_patch(self.selection_rect)



        image_plot.get_xaxis().set_visible(False)
        image_plot.get_yaxis().set_visible(False)
        image_plot.set_xlim(xmin=0,xmax=self.fixture_analysis_image.shape[1])
        image_plot.set_ylim(ymin=0,ymax=self.fixture_analysis_image.shape[0])
        image_canvas.show()
        image_canvas.set_size_request(int(round(image_size[1])), int(round(image_size[0])))
        hbox.pack_start(image_canvas, False, False, 2)
        self.image_fig.canvas.draw()

        #Grayscale view
        self.gs_view = gtk.VBox(False, 2)
        self.gs_view.show()
        hbox.pack_start(self.gs_view, False, False, 2)


        self.grayscale = grayscale.Gray_Scale(self)
        self.gs_view.pack_start(self.grayscale, False, False, 2)        

        #LIST containing the patch-objects of the graph.
        self.fixture_patches = []
        self.fixture_texts = []

        vbox3 = gtk.VBox(False, 0)
        vbox3.show()
        hbox.pack_end(vbox3, False, False, 0)

        #Fixture just viewing mode
        self.config_box_view = gtk.VBox(False, 0)
        vbox3.pack_start(self.config_box_view, False, False, 2)

        button = gtk.Button(label='Return to experiment setup')
        button.connect("clicked", owner.make_Experiment)
        button.show()
        self.config_box_view.pack_start(button, False, False, 2)

        #Fixture configure mode
        self.config_box_edit = gtk.VBox(False, 0)
        self.config_box_edit.show()
        vbox3.pack_start(self.config_box_edit, False, False, 2)

        hbox = gtk.HBox()
        hbox.show()
        self.config_box_edit.pack_start(hbox, False, False, 2)

        label = gtk.Label("Select image of fixture:")
        label.show()
        hbox.pack_start(label, False, False, 2)

        button = gtk.Button(label = 'Open')
        button.show()
        button.connect("clicked", self.select_image)
        hbox.pack_end(button, False, False, 2)

        self.fixture_image = gtk.Label("")
        self.fixture_image.set_max_width_chars(60)
        self.fixture_image.set_ellipsize(pango.ELLIPSIZE_START)
        self.fixture_image.show()
        self.config_box_edit.pack_start(self.fixture_image, False, False, 2)

        hbox = gtk.HBox()
        hbox.show()
        self.config_box_edit.pack_start(hbox, False, False, 2)

        label = gtk.Label("Select fixture marking image:")
        label.show()
        hbox.pack_start(label, False, False, 2)

        button = gtk.Button(label = 'Open')
        button.show()
        button.connect("clicked", self.select_marking)
        hbox.pack_end(button, False, False, 2)

        self.fixture_marking = gtk.Label("")
        self.fixture_marking.set_max_width_chars(50)
        self.fixture_marking.set_ellipsize(pango.ELLIPSIZE_MIDDLE)
        self.fixture_marking.show()
        self.config_box_edit.pack_start(self.fixture_marking, False, False, 2)

        hbox = gtk.HBox()
        hbox.show()
        self.config_box_edit.pack_start(hbox, False, False, 2)

        label = gtk.Label("Number of markings:")
        label.show()
        hbox.pack_start(label, False, False, 2)

        self.fixture_markings_count = gtk.Entry()
        self.fixture_markings_count.show()
        self.fixture_markings_count.set_text("")
        self.fixture_markings_count.connect("focus-out-event", self.verify_input, "int")
        hbox.pack_end(self.fixture_markings_count, False, False, 2)

        self.fixture_analysis_button = gtk.Button(label = 'Run analysis of markings placement')
        self.fixture_analysis_button.connect("clicked", self.marker_analysis)    
        self.fixture_analysis_button.show()
        self.config_box_edit.pack_start(self.fixture_analysis_button, False, False, 2)

        self.fixture_grayscale_checkbox = gtk.CheckButton(label="Grayscale", use_underline=False)
        self.fixture_grayscale_checkbox.show()
        self.fixture_grayscale_checkbox.connect("clicked", self.set_grayscale_toggle)
        self.config_box_edit.pack_start(self.fixture_grayscale_checkbox, False, False, 2)

        hbox = gtk.HBox()
        hbox.show()
        self.config_box_edit.pack_start(hbox, False, False, 2)

        label= gtk.Label("Plate Positions:")
        label.show()
        hbox.pack_start(label, False, False, 2)
 
        self.fixture_platepositions = gtk.Entry()
        self.fixture_platepositions.show()
        self.fixture_platepositions.set_text("4")
        #HACK NEED RE-IMPLEMENT
        #self.fixture_platepositions.connect("focus-out-event", self.areas_update, "int")
        #HACK END
        hbox.pack_end(self.fixture_platepositions, False, False, 2)

        frame = gtk.Frame("Area config")
        frame.show()
        self.config_box_edit.pack_start(frame, False, False, 2)

        vbox4 = gtk.VBox()
        vbox4.show()
        frame.add(vbox4)

        self.fixture_area_selection = gtk.combo_box_new_text()
        self.fixture_area_selection.show()
        self.fixture_area_selection.connect("changed", self.set_active_area)
        vbox4.pack_start(self.fixture_area_selection, False, False, 2)


        self.fixture_area_ul = gtk.Label("")
        self.fixture_area_ul.show()
        vbox4.pack_end(self.fixture_area_ul, False, False, 2)

        self.fixture_area_lr = gtk.Label("")
        self.fixture_area_lr.show()
        vbox4.pack_end(self.fixture_area_lr, False, False, 2)

        button = gtk.Button(label='Save fixture settings')
        button.show()
        button.connect("clicked", self.config_file_save)
        self.config_box_edit.pack_start(button, False, False, 2)


        self.DMS('fixture init', 'GUI loaded', 100)
        self.load_fixture_config()
        self.DMS('fixture init', 'Settings implemented', 100)

    #
    # FIXTURE VIEW MODE
    #
    def set_mode(self, widget=None, event=None, data=None):

        if event == 'view':
            self._fixture_gui_updating = True
            self.config_box_view.show()
            self.gs_view.hide()
            self.config_box_edit.hide()
        else:
            self._fixture_gui_updating = False
            self.config_box_view.hide()
            self.gs_view.show()
            self.config_box_edit.show()
            

    #
    # IMAGE OVERLAY FUNCTIONS
    #
    def set_fixture_overlay(self, area, text):

        #NO DUPLICATES
        for t_obj in self.fixture_texts:
            if text == t_obj.get_text():
                return None

        #FORMATTING DIFFER FOR GRAYSCALES
        lw = 2
        size = 'xx-large'
        try:
            int(text)
        except:
            lw = 1.0
            size = 'small'

        #GET THE PARAMETERS
        coordinate = area[0]
        width = area[1][0] - area[0][0]
        height = area[1][1] - area[0][1]
 
        #MAKE RECTANGLE
        rect = plt_patches.Rectangle(coordinate, width, height, 
            color = '#228822', fill=False, lw=lw, alpha=0.5)
        rect.get_axes()
        rect.get_transform()
        self.image_fig.gca().add_patch(rect)
        self.fixture_patches.append(rect)


        #MAKE TEXT
        text_obj = plt_text.Text(x=coordinate[0] + width/2.0, 
            y= coordinate[1] + height/2.0, text=text, 
            horizontalalignment='center', alpha=0.5, family='serif',
            verticalalignment='center',
            size = size, weight='bold', color='#001166')
        self.image_fig.gca().add_artist(text_obj)
        self.fixture_texts.append(text_obj) 

        #REDRAW CANVAS
        self.image_fig.canvas.draw()

        return rect

    def remove_fixture_overlay(self, by_object=None, by_name=None):


        for i in xrange(len(self.fixture_patches)):

            if (by_object is not None and \
                by_object == self.fixture_patches[i]) or \
                (by_name is not None and \
                by_name == self.fixture_texts[i].get_text()):

                self.image_fig.remove(self.fixture_patches[i])
                self.image_fig.remove(self.fixture_texts[i])
                del self.fixture_patches[i]
                del self.fixture_texts[i]
                break

    def change_fixture_overlay(self, area=None, by_object=None, by_name=None):

        
        for i in xrange(len(self.fixture_patches)):


            if (by_object is not None and \
                by_object == self.fixture_patches[i]) or \
                (by_name is not None and \
                by_name == self.fixture_texts[i].get_text()):
    
                if area is not None:
                    
                    coordinate = area[0]
                    width = area[1][0] - area[0][0]
                    height = -1 * (area[1][1] - area[0][1])

                    self.fixture_patches[i].set_xy(coordinate)
                    self.fixture_patches[i].set_width(width)
                    self.fixture_patches[i].set_height(-height)
                    self.fixture_texts[i].set_x(coordinate[0] + width/2.0)
                    self.fixture_texts[i].set_y(coordinate[1] - height/2.0)

                if by_name is not None:

                    self.fixture_texts[i].set_text(by_name)

                break

    def plot_click(self, event=None):

        
        if self._fixture_gui_updating == False:
            self.plot_ul = (event.xdata, event.ydata)
            self.selection_rect.set_x(event.xdata)
            self.selection_rect.set_y(event.ydata)
            self.plot_selecting = True

    def plot_move(self, event=None):

        if self.plot_selecting and event.xdata != None and event.ydata != None:
            self.selection_rect.set_width(    event.xdata - self.plot_ul[0])#,
            self.selection_rect.set_height(    event.ydata - self.plot_ul[1])#,
            self.image_fig.canvas.draw() 
            self.DMS("SELECTING", "Selecting something in the image", 1)

    def plot_release(self, event=None):

        if not self.plot_selecting:
            return None

        self.plot_selecting = False

        if event.xdata == None or event.ydata == None or \
            self.get_settings_name() is None:

            pass

        else:
            self.DMS("SELECTION", "UL: " + str(self.plot_ul) + ", LR: (" + 
                str(event.xdata) + ", "  +
                str(event.ydata) + ")", level=1)

                #self.fixture_active_pos(str((x_pos, y_pos)))
            lr = (event.xdata, event.ydata)
            area = [self.plot_ul, lr] 
            text = self.get_settings_initial()
            self.f_settings.fixture_config_file.set(self.get_settings_name(), area)
            
            self.change_fixture_overlay(by_name=text, area=area)
            self.fixture_area_ul.set_text( str(area[0]) )
            self.fixture_area_lr.set_text( str(area[1]) )

            if text == 'G':
                self.set_grayscale()

        self.selection_rect.set_width( 0 )
        self.selection_rect.set_height( 0 )
        self.image_fig.canvas.draw()


    #
    # SAVE CONFIG
    #

    def config_file_save(self, widget=None, event=None, data=None):
        self.f_settings.fixture_config_file.save()

    def get_settings_initial(self, active=None, text=None):

        if text is None:
            text = self.get_settings_name(active)
        if text == 'grayscale_area':
            text = "G"
        elif text is not None:
            text = text.split("_")[1]

        return text

    def get_settings_name(self, active = None):
            if active == None:
                active = self.fixture_area_selection.get_active()

            if active >= 1:
                active -= 1
                if self.fixture_grayscale_checkbox.get_active():
                    active -= 1 
                if active >= 0:
                    value_name = "plate_" + str(active)
                else:
                    value_name = "grayscale"

                value_name += "_area"

                return value_name
            else:
                return None

    def image_click(self, widget=None, event=None, data=None):
        vertOffset = float( self.fixture_scrolled_window.get_vadjustment().value )
        horzOffset = float( self.fixture_scrolled_window.get_hadjustment().value )
        
        if event:
            x_pos = (event.x + horzOffset)
            y_pos = (event.y + vertOffset)
            #print "x:", horzOffset, event.x, widget.get_allocation().x
            #print "y:", vertOffset, event.y, widget.get_allocation().y
        if self.fixture_active_pos != None and self.fixture_active_pos_setting != None:
            self.fixture_active_pos(str((x_pos, y_pos)))
            area = [eval(self.fixture_area_ul.get_text()), eval(self.fixture_area_lr.get_text())] 
            self.f_settings.fixture_config_file.set(self.get_settings_name(), area)

        else:
            self.DMS("Clicked Image", "Pos: " + str((x_pos, y_pos)), level=1)

    def marker_analysis(self, widget=None, event=None, data=None):
        analysis_img = self.f_settings.marker_analysis(fixture_setup=True)
        if analysis_img != None:
            self.fixture_analysis_image.set_from_file(analysis_img)
            self.fixture_scrolled_window.size_request()
        else:
            self.DMS("Error", "Image anaylsis failed", level = 1010)

    def select_image(self, widget=None, event=None, data=None):
        newimg = gtk.FileChooserDialog(title="Select new image", action=gtk.FILE_CHOOSER_ACTION_OPEN, 
            buttons=(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL, gtk.STOCK_APPLY, gtk.RESPONSE_APPLY))

        f = gtk.FileFilter()
        f.set_name("Valid image files")
        f.add_mime_type("image/tiff")
        f.add_pattern("*.tiff")
        f.add_pattern("*.TIFF")
        newimg.add_filter(f)

        result = newimg.run()
        
        if result == gtk.RESPONSE_APPLY:
            self.fixture_image.set_text(newimg.get_filename())
            self.f_settings.image_path = newimg.get_filename()
            self.fixture_image.cla()
            self.fixture_image.gca().imshow(newimg.get_filename(), cmap=plt.cm.gray)
            self.load_fixture_config()
            self.fixture_image.canvas.draw()
        newimg.destroy()

    def select_marking(self, widget=None, event=None, data=None):
        newimg = gtk.FileChooserDialog(title="Select marking image", action=gtk.FILE_CHOOSER_ACTION_OPEN, 
            buttons=(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL, gtk.STOCK_APPLY, gtk.RESPONSE_APPLY))

        f = gtk.FileFilter()
        f.set_name("Valid image files")
        f.add_mime_type("image/png")
        f.add_pattern("*.png")
        f.add_pattern("*.PNG")
        newimg.add_filter(f)

        result = newimg.run()
        
        if result == gtk.RESPONSE_APPLY:
            self.fixture_marking.set_text(newimg.get_filename())
            self.f_settings.marking_path = newimg.get_filename()
            try:
                self.f_settings.markings = int(self.fixture_markings_count.get_text())
            except ValueError:
                self.f_settings.markings = 0
 
            self.f_settings.fixture_config_file.set("marker_path",self.fixture_marking.get_text())
            self.f_settings.fixture_config_file.set("marker_count", self.f_settings.markings)
 
        newimg.destroy()

    def verify_input(self, widget=None, event=None, data=None):
        if widget:
            input_to_test = widget.get_text()        
            if data == "int":
                try:
                    int(input_to_test)
                    return True
                except ValueError:
                    widget.set_text("")
                    return False

            #HACK
            self.f_settings.markings = int(self.fixture_markings_count.get_text())
            self.f_settings.fixture_config_file.set("marker_count", self.f_settings.markings)

    def reset_drop_down(self):
                    
            #How much should be added?
            grayscales = self.get_grayscales()
            overlays = self.get_total_overlays()

            #Get what should be active afterwards
            active = self.fixture_area_selection.get_active()
            if active < 0:
                active = 0

            #Add first element
            self.fixture_area_selection.append_text("Select an area")
            self.current_fixture_settings = []

            #Add all other elements
            for i in xrange(overlays):

                if i == 0 and grayscales == 1:
                    self.fixture_area_selection.append_text("Grayscale")
                else:
                    self.fixture_area_selection.append_text("Plate " + str(i-grayscales))

                self.current_fixture_settings.append(" ")

            self.fixture_area_selection.set_active(active)
            self.fixture_area_selection.set_sensitive(len(self.current_fixture_settings) > 0)

    def set_grayscale(self):

        coords = self.f_settings.fixture_config_file.get("grayscale_area")
        xs = np.asarray((coords[0][0],coords[1][0]))
        ys = np.asarray((coords[0][1],coords[1][1]))
        im_section = self.fixture_analysis_image[xs.min():xs.max(), ys.min():ys.max()].copy()
        self.grayscale.clf()
        self.grayscale.set_grayscale(im_section.T)

    def load_fixture_config(self):

        self._fixture_gui_updating = True

        #
        # SET FILENAME OF MARKER
        #
        self.fixture_marking.set_text(str(\
            self.f_settings.fixture_config_file.get("marker_path")))

        #
        # SET NUMBER OF MARKERS EXPECTED
        #
        self.fixture_markings_count.set_text(str(\
            self.f_settings.fixture_config_file.get("marker_count")))

        #
        # SET IF THERE'S A GRAY-SCALE
        #
        grayscales = 1
        try:
            self.fixture_grayscale_checkbox.set_active(\
                self.f_settings.fixture_config_file.get("grayscale"))
        except TypeError:
            self.fixture_grayscale_checkbox.set_active(False)
            grayscales = 0


        if grayscale > 0:
            self.set_grayscale()
        #
        # SET UP DROP DOWN
        #
        self.reset_drop_down()            

        #
        # PRODUCE OVERLAYS
        #

        overlays = self.get_total_overlays() 
        for i in xrange(overlays):
            cur_area = self.f_settings.fixture_config_file.get(\
                self.get_settings_name(i+1))

            text = self.get_settings_initial(active=i+1)
            
            if cur_area != None:
                self.set_fixture_overlay(cur_area, text)

        self._fixture_gui_updating = False

    def get_grayscales(self):

        pos = 0
        if self.fixture_grayscale_checkbox.get_active():
            pos += 1

        return pos

    def get_total_overlays(self):

        pos = self.get_grayscales()

        if self.fixture_platepositions.get_text() != "":
            pos += int(self.fixture_platepositions.get_text())
        
        return pos
        
    def set_active_area(self, widget=None, event=None, data=None):
        if self._fixture_gui_updating == False:
            self._fixture_gui_updating = True

            active_name = self.get_settings_name()

            
            if active_name != None:
                cur_area = self.f_settings.fixture_config_file.get(active_name)
                if cur_area != None:
                    self.fixture_area_ul.set_text(str(cur_area[0]))
                    self.fixture_area_lr.set_text(str(cur_area[1]))
            else:
                self.fixture_area_ul.set_text("(N/A, N/A)")
                self.fixture_area_lr.set_text("(N/A, N/A)")
                self.fixture_area_selection.set_active(0)

            self._fixture_gui_updating = False

    def set_grayscale_toggle(self, widget=None, event=None, data=None):

        if self.fixture_grayscale_checkbox.get_active():
            self.f_settings.fixture_config_file.set("grayscale", True)
        else:
            self.f_settings.fixture_config_file.set("grayscale", False)
            self.f_settings.fixture_config_file.delete("grayscale_area")
            self.remove_fixture_overlay(by_name='G')

    #def areas_update(self, widget=None, event=None, data=None):
        #print "SHOULDN'T BE IN USE! areas update", widget, self._fixture_gui_updating
        #if self._fixture_gui_updating == False:
            #self._fixture_gui_updating = True
            #if widget:
                #if data == "int":
                    #self.verify_input(widget=widget, event=event, data=data)


            #overlays = self.get_total_overlays()

            #grayscales = self.get_grayscales()


            #if self.current_fixture_settings != None:
                #if len(self.current_fixture_settings) > overlays:
                    #for i in range(overlays, len(self.current_fixture_settings)):
#
                        #self.f_settings.fixture_config_file.delete(
                            #self.f_settings.settings_name(i))
#
                        #self.remove_fixture_overlay(by_name=\
                            #self.f_settings.settings_name(i))
#
            ##A BIT UGLY
            #if grayscales > 0:
                #self.f_settings.fixture_config_file.set('grayscale_area',[(-1,-1),(-1,-1)], overwrite=False)
#
            #if overlays > grayscales:
                #for p in xrange(overlays-grayscales):
                    #self.f_settings.fixture_config_file.set('plate_'+str(p)+'_area',[(-1,-1),(-1,-1)], overwrite=False)
#
            #active = self.fixture_area_selection.get_active()
            ##i = 0 #HACK!!
            #while i < 15:
                #self.fixture_area_selection.remove_text(0)
                #i += 1

#
            #if active < 0:
                #active = 0
            #else:
                #if active <= len(self.current_fixture_settings):
                    #self.fixture_area_selection.set_active(active)
                #else:
                    #self.fixture_area_selection.set_active(0)
#
            #self.fixture_area_selection.set_sensitive(len(self.current_fixture_settings) > 0)
#
            #self._fixture_gui_updating = False

        #return False
