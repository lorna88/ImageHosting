import os
from http.server import HTTPServer, BaseHTTPRequestHandler, SimpleHTTPRequestHandler
from uuid import uuid4
from loguru import logger
from os import listdir
from os.path import isfile, join
import json
import cgi
from PIL import Image

SERVER_ADDRESS = ('0.0.0.0', 8000)
ALLOWED_EXTENSIONS = ('.jpg', '.jpeg', '.png', '.gif')
ALLOWED_LENGTH = 5 * 1024 * 1024
UPLOAD_DIR = 'images'

logger.add('logs/app.log', format="[{time: YYYY-MM-DD HH:mm:ss}] | {level} | {message}")

class ImageHostingHandler(BaseHTTPRequestHandler):
    server_version = 'Image Hosting Server/0.1'

    def __init__(self, request, client_address, server):
        """Initialize the handler with routing for GET and POST requests."""
        self.get_routes = {
            '/upload': self.get_upload,
            '/images': self.get_images,
        }
        self.post_routes = {
            '/upload': self.post_upload,
        }
        super().__init__(request, client_address, server)

    def do_GET(self):
        if self.path in self.get_routes:
            self.get_routes[self.path]()
        else:
            logger.warning(f'GET 404 {self.path}')
            self.send_response(404, 'Not Found')

    def do_POST(self):
        if self.path in self.post_routes:
            self.post_routes[self.path]()
        else:
            logger.warning(f'POST 405 {self.path}')
            self.send_response(405, 'Method Not Allowed')

    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        SimpleHTTPRequestHandler.end_headers(self)

    def get_images(self):
        logger.info(f'GET {self.path}')
        self.send_response(200)
        self.send_header('Content-type', 'application/json; charset=utf-8')
        self.end_headers()

        images = [f for f in listdir(UPLOAD_DIR) if isfile(join('images', f))]
        logger.info(images)
        self.wfile.write(json.dumps({'images': images}).encode('utf-8'))

    def get_upload(self):
        logger.info(f'GET {self.path}')
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(open('upload.html', 'rb').read())

    def post_upload(self):
        logger.info(f'POST {self.path}')
        content_length = int(self.headers.get('Content-Length'))
        if content_length > ALLOWED_LENGTH:
            logger.error('Payload Too Large')
            self.send_response(413, 'Payload Too Large')
            return

        form = cgi.FieldStorage(
            fp=self.rfile,
            headers=self.headers,
            environ={'REQUEST_METHOD': 'POST'}
        )

        data = form['image'].file
        _, ext = os.path.splitext(form['image'].filename)

        if ext not in ALLOWED_EXTENSIONS:
            logger.error('Unsupported file extension')
            self.send_response(400, 'Unsupported file Extension')
            return

        image_id = uuid4()
        image_name = f'{image_id}{ext}'
        with open(f'{UPLOAD_DIR}/{image_name}', 'wb') as f:
            f.write(data.read())

        try:
            im = Image.open(f'{UPLOAD_DIR}/{image_name}')
            im.verify()
        except (IOError, SyntaxError) as e:
            logger.error(f'Invalid file: {e}')
            self.send_response(400, 'Invalid file')
            return

        logger.info(f'Upload success: {image_name}')
        self.send_response(301)
        self.send_header('Location', f'/images/{image_name}')
        self.end_headers()

def run(server_class=HTTPServer, handler_class=BaseHTTPRequestHandler):
    # noinspection PyTypeChecker
    httpd = server_class(SERVER_ADDRESS, handler_class)
    # noinspection PyBroadException
    try:
        logger.info(f'Serving at http://{SERVER_ADDRESS[0]}:{SERVER_ADDRESS[1]}')
        httpd.serve_forever()
    except BaseException:
        pass
    finally:
        logger.info('Server stopped')
        httpd.server_close()

if __name__ == '__main__':
    run(handler_class=ImageHostingHandler)