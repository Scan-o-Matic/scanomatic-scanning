__version__ = "0.9991"

import scanomatic.generics.model as model
from scanomatic.generics.enums import MinorMajorStepEnum
from enum import Enum


class SCAN_CYCLE(MinorMajorStepEnum):

    Wait = 0
    RequestScanner = 10
    WaitForUSB = 11
    ReportNotObtainedUSB = 12
    Scan = 20
    WaitForScanComplete = 21
    ReportScanError = 22
    RequestScannerOff = 30
    RequestFirstPassAnalysis = 40


class SCAN_STEP(Enum):

    Wait = 0
    NextMinor = 1
    NextMajor = 2


class PLATE_STORAGE(Enum):

    Unknown = -1
    Fresh = 0
    Cold = 1
    RoomTemperature = 2


class CULTURE_SOURCE(Enum):

    Unknown = -1
    Freezer80 = 0
    Freezer20 = 1
    Fridge = 2
    Shipped = 3
    Novel = 4


class ScanningAuxInfoModel(model.Model):

    def __init__(self, stress_level=-1, plate_storage=PLATE_STORAGE.Unknown, plate_age = -1.0,
                 pinning_project_start_delay=-1, precultures=-1, culture_freshness=-1,
                 culture_source=CULTURE_SOURCE.Unknown):

        self.stress_level = stress_level
        self.plate_storage=plate_storage
        self.plate_age = plate_age
        self.pinning_project_start_delay = pinning_project_start_delay
        self.precultures = precultures
        self.culture_freshness = culture_freshness
        self.culture_source = culture_source

        super(ScanningAuxInfoModel, self).__init__()


class ScanningModel(model.Model):

    def __init__(self, number_of_scans=217, time_between_scans=20,
                 project_name="", directory_containing_project="",
                 project_tag="", scanner_tag="", id="", start_time=0.0,
                 description="", email="", pinning_formats=tuple(),
                 fixture="", scanner=1, scanner_hardware="EPSON V700", mode="TPU",
                 auxillary_info=ScanningAuxInfoModel(),
                 plate_descriptions=tuple(),
                 version=__version__):

        self.number_of_scans = number_of_scans
        self.time_between_scans = time_between_scans
        self.project_name = project_name
        self.directory_containing_project = directory_containing_project
        self.project_tag = project_tag
        self.scanner_tag = scanner_tag
        self.id = id
        self.description = description
        self.plate_descriptions = plate_descriptions
        self.email = email
        self.pinning_formats = pinning_formats
        self.fixture = fixture
        self.scanner = scanner
        self.scanner_hardware = scanner_hardware
        self.mode = mode
        self.start_time = start_time
        self.auxillary_info = auxillary_info
        self.version = version

        super(ScanningModel, self).__init__()


class PlateDescription(model.Model):

    def __init__(self, name='', index=-1, description=''):

        if name is '':
            name = "Plate {0}".format(index + 1)

        self.name = name
        self.index = index
        self.description = description


class ScannerOwnerModel(model.Model):

    def __init__(self, socket=-1, scanner_name="", owner=None, usb="", power=False, last_on=-1, last_off=-1,
                 expected_interval=0, email="", warned=False, claiming=False, reported=False):

        self.socket = socket
        self.scanner_name = scanner_name
        self.usb = usb
        self.power = power
        self.last_on = last_on
        self.last_off = last_off
        self.expected_interval = expected_interval
        self.email = email
        self.warned = warned
        self.owner = owner
        self.claiming = claiming
        self.reported = reported

        super(ScannerOwnerModel, self).__init__()


class ScanningModelEffectorData(model.Model):

    def __init__(self, current_cycle_step=SCAN_CYCLE.Wait, current_step_start_time=-1, current_image=-1,
                 current_image_path="", current_image_path_pattern="",
                 project_time=-1.0, previous_scan_cycle_start=-1.0, current_scan_time=-1.0,
                 images_ready_for_first_pass_analysis=[],
                 scanning_image_name="", usb_port="", scanning_thread=None, scan_success=False,
                 compile_project_model=None):

        self.current_cycle_step = current_cycle_step
        self.current_step_start_time = current_step_start_time
        self.current_image = current_image
        self.current_image_path = current_image_path
        self.current_image_path_pattern = current_image_path_pattern
        self.project_time = project_time
        self.previous_scan_cycle_start = previous_scan_cycle_start
        self.current_scan_time = current_scan_time
        self.scanning_thread = scanning_thread
        self.scan_success = scan_success
        self.images_ready_for_first_pass_analysis = images_ready_for_first_pass_analysis
        self.scanning_image_name = scanning_image_name
        self.usb_port = usb_port
        self.compile_project_model = compile_project_model

        super(ScanningModelEffectorData, self).__init__()