from http.server import HTTPServer, BaseHTTPRequestHandler
from uuid import uuid4

SERVER_ADDRESS = ('localhost', 8000)
ALLOWED_EXTENSIONS = ('jpg', 'jpeg', 'png', 'gif')
ALLOWED_LENGTH = 5 * 1024 * 1024

class ImageHostingHandler(BaseHTTPRequestHandler):
    server_version = 'Image Hosting Server/0.1'
    def do_GET(self):
        if self.path in ('/', 'index.html'):
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(open('index.html', 'rb').read())
        else:
            self.send_response(404, 'Not Found')

    def do_POST(self):
        if self.path == '/upload':
            content_length = int(self.headers.get('Content-Length'))
            if content_length > ALLOWED_LENGTH:
                self.send_response(413, 'Payload Too Large')
                return

            # file_name = self.headers.get('filename')
            file_name = '1.jpg'
            if not file_name:
                self.send_response(400, 'Lack Of Filename Header')
                return

            filename, ext = file_name.rsplit('.', 1)
            if ext not in ALLOWED_EXTENSIONS:
                self.send_response(400, 'Unsupported file Extension')
                return

            data = self.rfile.read(content_length)
            image_id = uuid4()
            with open(f'images/{image_id}.{ext}', 'wb') as f:
                f.write(data)
            self.send_response(201)
            self.send_header('Location', f'http://{SERVER_ADDRESS[0]}:{SERVER_ADDRESS[1]}/images/{filename}.{ext}')
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(open('upload_success.html', 'rb').read())
        else:
            self.send_response(405, 'Method Not Allowed')

def run(server_class=HTTPServer, handler_class=BaseHTTPRequestHandler):
    httpd = server_class(SERVER_ADDRESS, handler_class)
    try:
        print(f'Serving at http://{SERVER_ADDRESS[0]}:{SERVER_ADDRESS[1]}')
        httpd.serve_forever()
    except BaseException:
        pass
    finally:
        httpd.server_close()

if __name__ == '__main__':
    run(handler_class=ImageHostingHandler)