#
# INTERNAL DEPENDENCIES
#

from src.model_generic import *

#
# MODELS
#

model = {

#ABOUT
##TOP
'mode-selection-top-fixture': 'Fixture',
'mode-selection-top-poly': 'Cell Count Polynomial',

##STAGE
'calibration-stage-about-text': """
<span size="x-large"><u>Calibration Options</u></span>

<span weight="heavy">Fixture</span>
<span><i>Fixture Calibration is done when a new fixture has been
constructed or to adjust an old fixture calibration. You will need
an image taken of the fixture in question.</i></span>

<span weight="heavy">Cell Count Polynomial</span>
<span><i>If a calibration experiment has been performed and the
results have been analysed, then here the csv-file can be used
to invoke a new calibration polynomial.</i></span>
""",

#FIXTURE SELECT
'fixture-select-title': """<span size="large">Fixture To Work With</span>""",

'fixture-select-radio-edit': 'Edit Existing Fixture:',
'fixture-select-radio-new': 'Create New Fixture:',
'fixture-select-column-header': 'Fixtures',
'fixture-select-new-name-duplicate': 'Illegal name, probably because it is a duplicate...',
'fixture-select-new-name-ok': 'Good choice!',
'fixture-select-next': 'Marker Calibration',

#FIXTURE MARKER CALIBRATION
'fixture-calibration-next': 'Segmenting Fixture',
'fixture-calibration-select-im': 'Select Image',
'fixture-calibration-marker-number': 'Number of calibration points',
'fixture-calibration-marker-detect': 'Run Detection',
'fixture-image-dialog': 'Select Image Using The Particular Fixture',
'fixture-image-file-filter': {'filter_name': 'Image Files',
'mime_and_patterns': (('IMAGE/TIFF', '*.[tT][iI][fF]'),
('IMAGE/TIF','*.[tT][iI][fF][fF]'))},

}


specific_fixture_model = {

'fixture': None,
'fixutre-file': None,
'new_fixture': False,
'original-image-path': None,
'im': None,
'im-path': None,
'im-scale': 1.0,
'im-not-loaded': 'No image selected',
'plate-coords': list(),
'markers': 0,
'marker-path': None,
'marker-positions': list()
}
