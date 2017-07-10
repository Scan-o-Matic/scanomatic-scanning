from flask import request, Flask, jsonify, send_from_directory
import os
import shutil
from enum import Enum
from ConfigParser import Error as ConfigError

from scanomatic.io.paths import Paths
from scanomatic.io.logger import Logger

from scanomatic.models.factories.fixture_factories import FixtureFactory

from .general import convert_url_to_path


_logger = Logger("Data API")


def add_routes(app, rpc_client, is_debug_mode):
    """

    Args:
        app (Flask): The flask app to decorate
        rpc_client (scanomatic.io.rpc_client._ClientProxy): A dynamic rpc-client bridge
        is_debug_mode (bool): If running in debug-mode
    """

    def _fixure_names():
        """Names of fixtures

        Returns: json-object with keys
            "fixtures" as the an array of strings, the names
            "success" if could be obtained and if not "reason" to explain why.

        """

        if rpc_client.online:
            return jsonify(fixtures=rpc_client.get_fixtures(), success=True)
        else:
            return jsonify(fixtures=[], success=False, reason="Scan-o-Matic server offline")

    @app.route("/api/data/fixture/local/<path:project>")
    @app.route("/api/data/fixture/local")
    def _fixture_local_data(project=""):

        path = os.path.join(convert_url_to_path(project), Paths().experiment_local_fixturename)

        try:
            fixture = FixtureFactory.serializer.load_first(path)
            if fixture is None:
                return jsonify(
                    success=False,
                    reason="File is missing")
            return jsonify(
                success=True, grayscale=dict(**fixture.grayscale),
                plates=[dict(**plate) for plate in fixture.plates],
                markers=zip(fixture.orientation_marks_x, fixture.orientation_marks_y))
        except IndexError:
            return jsonify(success=False, reason="Fixture without data")
        except ConfigError:
            return jsonify(success=False, reason="Fixture data corrupted")

    @app.route("/api/data/fixture/get/<name>")
    def _fixture_data(name=None):
        """Get the specifications of a fixture

        Args:
            name: The name of the fixture

        Returns: json-object where keys:
            "plates" is an array of key-value arrays of the
                included plates specs
            "grayscale" is a key-value array of its specs
            "markers" is a 2D array of the marker centra
            "success" if the fixture was found and valid else
            "reason" to explain why not.

        """
        if not rpc_client.online:
            return jsonify(success=False, reason="Scan-o-Matic server offline")
        elif name in rpc_client.get_fixtures():
            path = Paths().get_fixture_path(name)
            try:
                fixture = FixtureFactory.serializer.load_first(path)
                if fixture is None:
                    return jsonify(
                        success=False,
                        reason="File is missing"
                    )
                return jsonify(
                    success=True, grayscale=dict(**fixture.grayscale),
                    plates=[dict(**plate) for plate in fixture.plates],
                    markers=zip(fixture.orientation_marks_x, fixture.orientation_marks_y))
            except IndexError:
                return jsonify(success=False, reason="Fixture without data")
            except ConfigError:
                return jsonify(success=False, reason="Fixture data corrupted")
        else:
            return jsonify(success=False, reason="Unknown fixture")

    @app.route("/api/data/fixture/remove/<name>")
    def _fixture_remove(name):
        """Remove a fixture by name

        Args:
            name: The name of the fixture to remove

        Returns: json-object with keys
            "success" if removed else
            "reason" to explain why not.

        """
        name = Paths().get_fixture_name(name)
        known_fixtures = tuple(Paths().get_fixture_name(f) for f in rpc_client.get_fixtures())
        if name not in known_fixtures:
            return jsonify(success=False, reason="Unknown fixture")
        source = Paths().get_fixture_path(name)
        path, ext = os.path.splitext(source)
        i = 0
        pattern = "{0}.deleted{1}"
        while os.path.isfile(pattern.format(path, i)):
            i += 1
        try:
            shutil.move(source, pattern.format(path, i))
        except IOError:
            return jsonify(success=False, reason="Error while removing")
        return jsonify(success=True, reason="Happy")

    @app.route("/api/data/fixture/image/get/<name>")
    def _fixture_get_image(name):
        """Get downscaled png image for the fixture.

        Args:
            name: Name of the fixture

        Returns: image

        """
        image = os.path.extsep.join((name, "png"))
        _logger.info("Sending fixture image {0}".format(image))
        return send_from_directory(Paths().fixtures, image)

    # End of adding routes
