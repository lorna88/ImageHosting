from http.server import HTTPServer, BaseHTTPRequestHandler, SimpleHTTPRequestHandler
from uuid import uuid4
from loguru import logger
from os import listdir
from os.path import isfile, join
import json

SERVER_ADDRESS = ('0.0.0.0', 8000)
ALLOWED_EXTENSIONS = ('jpg', 'jpeg', 'png', 'gif')
ALLOWED_LENGTH = 5 * 1024 * 1024

logger.add('logs/app.log', format="[{time: YYYY-MM-DD HH:mm:ss}] | {level} | {message}")

class ImageHostingHandler(BaseHTTPRequestHandler):
    server_version = 'Image Hosting Server/0.1'

    routes = {
        '/': 'get_index',
        '/index.html': 'get_index',
        '/upload': 'post_upload',
        '/images': 'get_images',
    }

    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        SimpleHTTPRequestHandler.end_headers(self)

    def do_GET(self):
        if self.path in self.routes:
            exec(f'self.{self.routes[self.path]}()')
        else:
            logger.warning(f'GET 404 {self.path}')
            self.send_response(404, 'Not Found')

    def get_index(self):
        logger.info(f'GET {self.path}')
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(open('static/index.html', 'rb').read())

    def get_images(self):
        logger.info(f'GET {self.path}')
        self.send_response(200)
        self.send_header('Content-type', 'application/json; charset=utf-8')
        self.end_headers()

        images = [f for f in listdir('./images') if isfile(join('./images', f))]
        logger.info(images)
        self.wfile.write(json.dumps({'images': images}).encode('utf-8'))

    def do_POST(self):
        if self.path == '/upload':
            exec(f'self.{self.routes[self.path]}()')
        else:
            logger.warning(f'POST 405 {self.path}')
            self.send_response(405, 'Method Not Allowed')

    def post_upload(self):
        logger.info(f'POST {self.path}')
        content_length = int(self.headers.get('Content-Length'))
        if content_length > ALLOWED_LENGTH:
            logger.error('Payload Too Large')
            self.send_response(413, 'Payload Too Large')
            return

        # file_name = self.headers.get('filename')
        file_name = '1.jpg'
        if not file_name:
            logger.error('Lack of Filename header')
            self.send_response(400, 'Lack Of Filename Header')
            return

        filename, ext = file_name.rsplit('.', 1)
        if ext not in ALLOWED_EXTENSIONS:
            logger.error('Unsupported file extension')
            self.send_response(400, 'Unsupported file Extension')
            return

        data = self.rfile.read(content_length)
        image_id = uuid4()
        with open(f'images/{image_id}.{ext}', 'wb') as f:
            f.write(data)
        logger.info(f'Upload success: {image_id}.{ext}')
        self.send_response(201)
        self.send_header('Location', f'http://{SERVER_ADDRESS[0]}:{SERVER_ADDRESS[1]}/images/{filename}.{ext}')
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(open('upload_success.html', 'rb').read())

def run(server_class=HTTPServer, handler_class=BaseHTTPRequestHandler):
    httpd = server_class(SERVER_ADDRESS, handler_class)
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