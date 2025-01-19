from flask import Flask, Response, render_template_string
import cv2
from pyzbar.pyzbar import decode
import webbrowser
import threading

app = Flask(__name__)

# Initialize the camera
cap = cv2.VideoCapture(0)
if not cap.isOpened():
    raise Exception("Could not access the camera.")

processed_codes = {}  # Dictionary to track QR codes and their statuses

@app.route("/")
def index():
    """Render the main page."""
    return render_template_string("""
    <html>
    <head>
        <title>QR Code Scanner</title>
    </head>
    <body>
        <h1>QR Code Scanner</h1>
        <p>Point your webcam at a QR code.</p>
        <p>Detected URLs will open automatically in your browser.</p>
        <img src="/video_feed" width="640" height="480" />
    </body>
    </html>
    """)

def handle_qr_data(data):
    """Handle QR code data, opening URLs in the browser if necessary."""
    if data.startswith("http://") or data.startswith("https://"):
        if data not in processed_codes or not processed_codes[data]:
            try:
                webbrowser.open(data)
                processed_codes[data] = True  # Mark as successfully opened
                print(f"Opened URL: {data}")
            except Exception as e:
                processed_codes[data] = False  # Mark as failed
                print(f"Error opening URL {data}: {e}")
    else:
        print(f"No action defined for: {data}")

def generate_frames():
    """Generate video frames for the web interface."""
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        qr_codes = decode(frame)
        for qr in qr_codes:
            qr_data = qr.data.decode('utf-8')
            if qr_data not in processed_codes:
                processed_codes[qr_data] = False  # Initialize as not processed

            # If unprocessed or previously failed, process it
            if not processed_codes[qr_data]:
                handle_qr_data(qr_data)

            # Draw bounding box and show the QR data
            x, y, w, h = qr.rect
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
            text = f"{qr.type}: {qr_data}"
            cv2.putText(frame, text, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)

        _, buffer = cv2.imencode('.jpg', frame)
        frame = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

@app.route("/video_feed")
def video_feed():
    """Video feed route."""
    return Response(generate_frames(), mimetype="multipart/x-mixed-replace; boundary=frame")

if __name__ == "__main__":
    # Run the Flask app
    app.run(host="0.0.0.0", port=5000, debug=True)
