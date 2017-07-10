from flask import request, Flask, jsonify
from itertools import product, chain
import os
import glob
from urllib import unquote

from scanomatic.ui_server.general import safe_directory_name
from scanomatic.io.app_config import Config
from scanomatic.io.logger import Logger, parse_log_file
from scanomatic.io.paths import Paths
from .general import convert_url_to_path, json_response, serve_zip_file

_logger = Logger("Tools API")


def valid_range(settings):
    return 'min' in settings and 'max' in settings


def add_routes(app):

    """

    Args:
        app (Flask): The flask app to decorate
    """

    @app.route("/api/tools/system_logs")
    @app.route("/api/tools/system_logs/<what>/<detail>")
    @app.route("/api/tools/system_logs/<what>")
    def system_log_view(what=None, detail=None):

        base_url = "/api/tools/system_logs"
        if what == 'server':
            what = Paths().log_server
        elif what == "ui_server":
            what = Paths().log_ui_server
        elif what == "scanner_error":
            if detail is None:
                return jsonify(success=False, is_endpoint=True,
                               reason="{0} needs to know what scanner log detail".format(what))
            what = Paths().log_scanner_err.format(detail)
        elif what == "scanner":
            if detail is None:
                return jsonify(success=False, is_endpoint=True,
                               reason="{0} needs to know what scanner log detail".format(what))
            what = Paths().log_scanner_out.format(detail)
        else:

            return jsonify(**json_response(
                ['urls'],
                dict(
                    urls=["{0}/{1}".format(base_url, w) for w in ('server', 'ui_server', 'scanner', 'scanner_error')]
                )
            ))

        try:
            data = parse_log_file(what)
        except IOError:
            return jsonify(success=False, is_endpoint=True, reason="No log-file found with that name")

        return jsonify(success=True, is_endpoint=True, **{k: v for k, v in data.iteritems() if k not in ('file',)})

    @app.route("/api/tools/logs")
    @app.route("/api/tools/logs/<filter_status>/<path:project>")
    @app.route("/api/tools/logs/<int:n_records>/<path:project>")
    @app.route("/api/tools/logs/<filter_status>/<int:n_records>/<path:project>")
    @app.route("/api/tools/logs/<int:start_at>/<int:n_records>/<path:project>")
    @app.route("/api/tools/logs/<filter_status>/<int:start_at>/<int:n_records>/<path:project>")
    def log_view(project='', filter_status=None, n_records=-1, start_at=0):

        # base_url = "/api/tools/logs"
        path = convert_url_to_path(project)
        if n_records == 0:
            n_records = -1

        try:
            data = parse_log_file(path, seek=start_at, max_records=n_records, filter_status=filter_status)
        except IOError:
            return jsonify(success=False, is_endpoint=True, reason="No log-file found with that name")

        return jsonify(success=True, is_endpoint=True, **{k: v for k, v in data.iteritems() if k not in ('file',)})

    @app.route("/api/tools/selection", methods=['POST'])
    @app.route("/api/tools/selection/<operation>", methods=['POST'])
    def tools_create_selection(operation='rect'):
        """Converts selection ranges to api-understood selections.

        _Note_ that the range-boundary uses inclusive min and
        exclusive max indices.

        Query should be json-formatted and each key to be used must
        have the following structure

        ```key: {min: min_value, max: max_value}```

        Args:
            operation: Optional, 'rect' is default.
                Defines how the selection should be made
                * if 'rect' then supplied json-key ranges are treated as
                    combined bounding box coordinates
                * if 'separate' each json-key range is converted
                    individually.


        Returns: json-object containing the same keys as the object sent.

        """
        data_object = request.get_json(silent=True, force=True)
        if not data_object:
            data_object = request.values

        if data_object is None or len(data_object) == 0:
            return jsonify(success=False, reason="No valid json or post is empty")

        if operation == 'separate':
            response = {}
            for key in data_object:

                settings = data_object.get(key)

                if valid_range(settings):
                    response[key] = range(settings['min'], settings['max'])

            return jsonify(**response)

        elif operation == 'rect':
            return jsonify(
                **{k: v for k, v in
                   zip(data_object,
                       zip(*product(*(range(v['min'], v['max'])
                                      for k, v in data_object.iteritems()
                                      if valid_range(v)))))})

        else:
            return jsonify()

    @app.route("/api/tools/coordinates", methods=['POST'])
    @app.route("/api/tools/coordinates/<operation>", methods=['POST'])
    def tools_coordinates(operation='create'):
        """Conversion between coordinates and api selections.

        Coordinates are (x, y) positions.

        Selections are separate arrays of X and Y that combined
        makes coordinates.

        Args:
            operation: Optional, default 'create'
                * if 'create' uses the keys supplied in 'keys' or all
                    keys POSTed to create coordinates.
                * if 'parse' converts a list of coordinates under the
                    POSTed key 'coordinates' to selection structure.
        Returns: json-object

        """
        data_object = request.get_json(silent=True, force=True)
        if not data_object:
            data_object = request.values

        if operation == 'create':
            keys = data_object.get('keys', data_object.keys())
            return jsonify(coordinates=zip(*(data_object[k] for k in keys)))

        elif operation == 'parse':
            _logger.info("Parsing {0}".format(data_object))
            if 'coordinates' in data_object:
                return jsonify(selection=zip(*data_object['coordinates']))
            else:
                return jsonify(success=False, reason="No coordinates in {0}".format(data_object))

    # End of adding routes
