import os
import requests
import glob
import time
import webbrowser
from flask import Flask, request, send_from_directory, redirect, jsonify, render_template
from flask_cors import CORS

from socket import error
from threading import Thread, Timer
from types import StringTypes

from scanomatic.io.app_config import Config
from scanomatic.io.logger import Logger, LOG_RECYCLE_TIME
from scanomatic.io.paths import Paths
from scanomatic.io.power_manager import POWER_MANAGER_TYPE
from scanomatic.io.rpc_client import get_client
from scanomatic.models.compile_project_model import COMPILE_ACTION
from scanomatic.models.factories.scanning_factory import ScanningModelFactory
from scanomatic.io.backup import backup_file

from . import scan_api
from . import management_api
from . import tools_api
from . import data_api
from .general import (
    get_2d_list, serve_log_as_html, convert_url_to_path, get_search_results,
    convert_path_to_url
)

_url = None
_logger = Logger("UI-server")
_debug_mode = None


def init_logging():

    _logger.pause()
    backup_file(Paths().log_ui_server)
    _logger.set_output_target(
        Paths().log_ui_server,
        catch_stdout=_debug_mode is False, catch_stderr=_debug_mode is False)
    _logger.surpress_prints = _debug_mode is False
    _logger.resume()


def launch_server(host, port, debug):

    global _url, _debug_mode
    _debug_mode = debug
    app = Flask("Scan-o-Matic UI", template_folder=Paths().ui_templates)

    rpc_client = get_client(admin=True)

    if rpc_client.local and rpc_client.online is False:
        rpc_client.launch_local()

    if port is None:
        port = Config().ui_server.port
    if host is None:
        host = Config().ui_server.host

    _url = "http://{host}:{port}".format(host=host, port=port)
    init_logging()
    _logger.info("Requested to launch UI-server at {0} being debug={1}".format(
        _url, debug))

    app.log_recycler = Timer(LOG_RECYCLE_TIME, init_logging)
    app.log_recycler.start()

    @app.route("/")
    def _root():
        return render_template(Paths().ui_root_file, debug=app.debug)

    @app.route("/ccc")
    def _ccc():
        return send_from_directory(Paths().ui_root, Paths().ui_ccc_file)

    @app.route("/help")
    def _help():
        return send_from_directory(Paths().ui_root, Paths().ui_help_file)

    @app.route("/qc_norm")
    def _qc_norm():
        return send_from_directory(Paths().ui_root, Paths().ui_qc_norm_file)

    @app.route("/wiki")
    def _wiki():
        return redirect("https://github.com/local-minimum/scanomatic/wiki")

    @app.route("/maintain")
    def _maintain():
        return send_from_directory(Paths().ui_root, Paths().ui_maintain_file)

    @app.route("/images/<image_name>")
    def _help_logo(image_name=None):
        if image_name:
            return send_from_directory(Paths().images, image_name)

    @app.route("/style/<style>")
    def _css_base(style=None):
        if style:
            return send_from_directory(Paths().ui_css, style)

    @app.route("/js/<js>")
    def _js_base(js=None):
        if js:
            return send_from_directory(Paths().ui_js, js)

    @app.route("/fonts/<font>")
    def _font_base(font=None):
        if font:
            return send_from_directory(Paths().ui_font, font)

    @app.route("/home")
    def _show_homescreen():
        return redirect("/status")

    @app.route("/logs/system/<log>")
    def _logs(log):
        """
        Args:
            log: The log-type to be returned {'server' or 'ui_server'}.

        Returns: html-document (or json on invalid log-parameter).

        """
        if log == 'server':
            log_path = Paths().log_server
        elif log == "ui_server":
            log_path = Paths().log_ui_server
        else:
            return jsonify(success=False, is_endpoint=True, reason="No system log of that type")

        return serve_log_as_html(log_path, log.replace("_", " ").capitalize())

    @app.route("/logs/project/<path:project>")
    def _project_logs(project):

        path = convert_url_to_path(project)

        if not os.path.exists(path):

            return jsonify(success=True,
                           is_project=False,
                           is_endpoint=False,
                           exits=['urls'],
                           **get_search_results(path, "/logs/project"))

        is_project_analysis = phenotyper.path_has_saved_project_state(path)

        if not os.path.isfile(path) or not path.endswith(".log"):

            if is_project_analysis:
                logs = glob.glob(os.path.join(path, Paths().analysis_run_log))
                logs += glob.glob(os.path.join(path, Paths().phenotypes_extraction_log))
            else:
                logs = glob.glob(os.path.join(path, Paths().scan_log_file_pattern.format("*")))
                logs += glob.glob(os.path.join(path, Paths().project_compilation_log_pattern.format("*")))

            return jsonify(success=True,
                           is_project=False,
                           is_endpoint=False,
                           is_project_analysis=is_project_analysis,
                           exits=['urls', 'logs'],
                           logs=[convert_path_to_url("/logs/project", log_path) for log_path in logs],
                           **get_search_results(path, "/logs/project"))

        include_levels = 3 if is_project_analysis else 2

        return serve_log_as_html(path, os.sep.join(path.split(os.path.sep)[-include_levels:]))

    @app.route("/status")
    @app.route("/status/<status_type>")
    def _status(status_type=""):

        if status_type != "" and not rpc_client.online:
            return jsonify(success=False, reason="Server offline")

        if status_type == 'queue':
            return jsonify(success=True, data=rpc_client.get_queue_status())
        elif 'scanner' in status_type:
            return jsonify(success=True, data=rpc_client.get_scanner_status())
        elif 'job' in status_type:
            data = rpc_client.get_job_status()
            for item in data:
                if item['type'] == "Feature Extraction Job":
                    item['label'] = convert_path_to_url("", item['label'])
                if 'log_file' in item and item['log_file']:
                    item['log_file'] = convert_path_to_url("/logs/project", item['log_file'])
            return jsonify(success=True, data=data)
        elif status_type == 'server':
            return jsonify(success=True, data=rpc_client.get_status())
        elif status_type == "":

            return send_from_directory(Paths().ui_root, Paths().ui_status_file)
        else:
            return jsonify(succes=False, reason='Unknown status request')

    @app.route("/settings", methods=['get', 'post'])
    def _config():

        app_conf = Config()

        action = request.args.get("action")
        if action == "update":

            data_object = request.get_json(silent=True, force=True)
            if not data_object:
                data_object = request.values

            app_conf.number_of_scanners = data_object["number_of_scanners"]
            app_conf.power_manager.number_of_sockets = data_object["power_manager"]["sockets"]
            app_conf.power_manager.host = data_object["power_manager"]["host"]
            app_conf.power_manager.mac = data_object["power_manager"]["mac"]
            app_conf.power_manager.name = data_object["power_manager"]["name"]
            app_conf.power_manager.password = data_object["power_manager"]["password"]
            app_conf.power_manager.host = data_object["power_manager"]["host"]
            app_conf.power_manager.type = POWER_MANAGER_TYPE[data_object["power_manager"]["type"]]
            app_conf.paths.projects_root = data_object["paths"]["projects_root"]
            app_conf.computer_human_name = data_object["computer_human_name"]
            app_conf.mail.warn_scanning_done_minutes_before = data_object["mail"]["warn_scanning_done_minutes_before"]

            bad_data = []
            success = app_conf.validate(bad_data)
            app_conf.save_current_settings()
            return jsonify(success=success, reason=None if success else "Bad data for {0}".format(bad_data))
        elif action:
            return jsonify(success=False, reason="Not implemented")

        return render_template(Paths().ui_settings_template, **app_conf.model_copy())

    @app.route("/experiment", methods=['get', 'post'])
    def _experiment():

        if request.args.get("enqueue"):

            data_object = request.get_json(silent=True, force=True)
            if not data_object:
                data_object = request.values

            project_name = os.path.basename(os.path.abspath(data_object.get("project_path")))
            project_root = os.path.dirname(data_object.get("project_path")).replace(
                'root', Config().paths.projects_root)

            plate_descriptions = data_object.get("plate_descriptions")
            if all(isinstance(p, StringTypes) or p is None for p in plate_descriptions):
                plate_descriptions = tuple({"index": i, "description": p} for i, p in enumerate(plate_descriptions))

            m = ScanningModelFactory.create(
                 number_of_scans=data_object.get("number_of_scans"),
                 time_between_scans=data_object.get("time_between_scans"),
                 project_name=project_name,
                 directory_containing_project=project_root,
                 project_tag=data_object.get("project_tag"),
                 scanner_tag=data_object.get("scanner_tag"),
                 description=data_object.get("description"),
                 email=data_object.get("email"),
                 pinning_formats=data_object.get("pinning_formats"),
                 fixture=data_object.get("fixture"),
                 scanner=data_object.get("scanner"),
                 scanner_hardware=data_object.get("scanner_hardware") if "scanner_hardware" in request.json
                 else "EPSON V700",
                 mode=data_object.get("mode", "TPU"),
                 plate_descriptions=plate_descriptions,
                 auxillary_info=data_object.get("auxillary_info"),
            )

            validates = ScanningModelFactory.validate(m)

            job_id = rpc_client.create_scanning_job(ScanningModelFactory.to_dict(m))

            if validates and job_id:
                return jsonify(success=True, name=project_name)
            else:

                return jsonify(success=False, reason="The following has bad data: {0}".format(
                    ScanningModelFactory.get_invalid_as_text(m))
                    if not validates else
                    "Job refused, probably scanner can't be reached, check connection.")

        return send_from_directory(Paths().ui_root, Paths().ui_experiment_file)

    @app.route("/scanners/<scanner_query>")
    def _scanners(scanner_query=None):
        if scanner_query is None or scanner_query.lower() == 'all':
            return jsonify(scanners=rpc_client.get_scanner_status(), success=True)
        elif scanner_query.lower() == 'free':
            return jsonify(scanners={s['socket']: s['scanner_name'] for s in rpc_client.get_scanner_status()
                                     if 'owner' not in s or not s['owner']},
                           success=True)
        else:
            try:
                return jsonify(scanner=(s for s in rpc_client.get_scanner_status() if scanner_query
                                        in s['scanner_name']).next(), success=True)
            except StopIteration:
                return jsonify(scanner=None, success=False, reason="Unknown scanner or query '{0}'".format(
                    scanner_query))

    @app.route("/fixtures", methods=['post', 'get'])
    def _fixtures():

        return send_from_directory(Paths().ui_root, Paths().ui_fixture_file)

    management_api.add_routes(app, rpc_client)
    tools_api.add_routes(app)
    scan_api.add_routes(app)
    data_api.add_routes(app, rpc_client, debug)

    if debug:
        CORS(app)
        _logger.warning(
            "\nRunning in debug mode, causes sequrity vunerabilities:\n" +
            " * Remote code execution\n" +
            " * Cross-site request forgery\n" +
            "   (https://en.wikipedia.org/wiki/Cross-site_request_forgery)\n" +
            "\nAnd possibly more issues"

        )
    try:
        app.run(port=port, host=host, debug=debug)
    except error:
        _logger.warning(
            "Could not bind socket, probably server is already running and" +
            " this is nothing to worry about." +
            "\n\tIf old server is not responding, try killing its process." +
            "\n\tIf something else is blocking the port," +
            " try setting another port" +
            " (see `scan-o-matic --help` for instructions).")
        return False
    return True


def launch_webbrowser(delay=0.0):

    if delay:
        _logger.info("Will open webbrowser in {0} s".format(delay))
        time.sleep(delay)

    if _url:
        webbrowser.open(_url)
    else:
        _logger.error("No server launched")


def launch(host, port, debug, open_browser_url=True):
    if open_browser_url:
        _logger.info("Getting ready to open browser")
        Thread(target=launch_webbrowser, kwargs={"delay": 2}).start()
    else:
        _logger.info("Will not open browser")

    launch_server(host, port, debug)


def ui_server_responsive():

    port = Config().ui_server.port
    if not port:
        port = 5000
    host = Config().ui_server.host
    if not host:
        host = 'localhost'
    try:
        return requests.get("http://{0}:{1}".format(host, port)).ok
    except requests.ConnectionError:
        return False
