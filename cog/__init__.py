import logging
import os
import json
import base64
import io

from flask import Flask, request, send_file, abort, jsonify

from rio_tiler import main
from rio_tiler.utils import array_to_image
from rio_tiler.profiles import img_profiles
from rio_tiler_mosaic.mosaic import mosaic_tiler
from rio_tiler_mosaic.methods import defaults

from rio_tiler.errors import TileOutsideBounds

import CTRegisterMicroserviceFlask


PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE_DIR = os.path.dirname(PROJECT_DIR)

#Load swager and register files so we can register them aginst controlTower
def load_config_json(name):
    json_path = os.path.abspath(os.path.join(BASE_DIR, f'/microservice/{name}.json'))
    with open(json_path) as data_file:
        info = json.load(data_file)
    return info

# Set App logs
logging.basicConfig(
    level=SETTINGS.get('logging', {}).get('level'),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y%m%d-%H:%M%p',

)
# App options
image_options = img_profiles["png"]

# Flask App
app = Flask(__name__)

@app.route('/cog/<b64url>/<z>/<x>/<y>/',  strict_slashes=False, methods=['GET'])
def tile(b64url, x, y, z):
    url = str(base64.b64decode(b64url).decode('utf-8'))
    app.logger.debug(f"Getting tile z {z} x {x} y {y} at url {url}")
    try:


assets = ["mytif1.tif", "mytif2.tif", "mytif3.tif"]
tile = (1000, 1000, 9)
x, y, z = tile

# Use Default First value method
mosaic_tiler(assets, x, y, z, cogTiler)

        tile, mask = main.tile(
            url,
            int(x),
            int(y),
            int(z),
            tilesize=256
        )
    except TileOutsideBounds as e:
        app.logger.debug("Tile out of bounds")
        return abort(404)
    
    _buffer = array_to_image(tile, mask=mask, img_format="png", **image_options)
    del tile, mask
    return send_file(
        io.BytesIO(_buffer),
        mimetype='image/png',
        as_attachment=False,
        attachment_filename='tile.jpg'
    )

@app.route('/cog/<b64url>/',  strict_slashes=False, methods=['GET'])
def metadata(b64url):
    url = str(base64.b64decode(b64url).decode('utf-8'))
    app.logger.debug(f"Getting metadata at url {url}")
    try:
        metadata = main.metadata(url)
        app.logger.debug(metadata)
    except Exception as e:
        app.logger.debug(e)
        return abort(500)
    return jsonify(metadata)


# CT
info = load_config_json('register')
swagger = load_config_json('swagger')
CTRegisterMicroserviceFlask.register(
    app=app,
    name='cog-tiles',
    info=info,
    swagger=swagger,
    mode=CTRegisterMicroserviceFlask.AUTOREGISTER_MODE if os.getenv('CT_REGISTER_MODE') and os.getenv('CT_REGISTER_MODE') == 'auto' else CTRegisterMicroserviceFlask.NORMAL_MODE,
    ct_url=os.getenv('CT_URL'),
    url=os.getenv('LOCAL_URL')
)

@app.errorhandler(403)
def forbidden(e):
    return error(status=403, detail='Forbidden')


@app.errorhandler(404)
def page_not_found(e):
    return error(status=404, detail='Not Found (404)')


@app.errorhandler(405)
def method_not_allowed(e):
    return error(status=405, detail='Method Not Allowed')


@app.errorhandler(410)
def gone(e):
    return error(status=410, detail='Gone')


@app.errorhandler(500)
def internal_server_error(e):
    return error(status=500, detail='Internal Server Error')

