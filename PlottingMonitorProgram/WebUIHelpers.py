import http 
import threading 
import socketserver 


class ProjectorRequestHandler(http.server.SimpleHTTPRequestHandler):
      def __init__(self, html_path):
                self.html_path = html_path 

      def do_GET(self):
                if self.path in ("/", "/index.html", "/channel_plot_projector.html","/channel_monitor.html"):
                    try:
                        with open(self.html_path, "rb") as f:
                            content = f.read()
                        self.send_response(200)
                        self.send_header("Content-Type", "text/html; charset=utf-8")
                        self.send_header("Content-Length", str(len(content)))
                        self.end_headers()
                        self.wfile.write(content)
                    except FileNotFoundError:
                        self.send_error(404, "channel_plot_projector.html not found")
                else:
                    self.send_error(404, "Not Found")

      def log_message(self, format, *args):
                # Suppress noisy console HTTP logs
                pass



class ReusableTCPServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
            allow_reuse_address = True
            daemon_threads = True
