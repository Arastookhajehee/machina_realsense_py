import cv2
import numpy as np
from mc_client import machina_client
import datetime
import pyrealsense2 as rs
# Define HSV color range for green
lower_green = np.array([40, 70, 70])
upper_green = np.array([80, 255, 255])

current_time = datetime.datetime.now()

machina = machina_client("ws://127.0.0.1:6999/Bridge")           

# RealSense initialization
pipeline = rs.pipeline()
config = rs.config()
config.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 30)
pipeline.start(config)

try:
    while True:
        # Get color frame from RealSense
        frames = pipeline.wait_for_frames()
        color_frame = frames.get_color_frame()
        if not color_frame:
            continue

        frame = np.asanyarray(color_frame.get_data())
        height, width = frame.shape[:2]
        center_x = width // 2
        center_y = height // 2

        # Convert to HSV and apply green mask
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        mask = cv2.inRange(hsv, lower_green, upper_green)

        # Clean the mask
        kernel = np.ones((5, 5), np.uint8)
        mask = cv2.erode(mask, kernel, iterations=1)
        mask = cv2.dilate(mask, kernel, iterations=2)

        # Find contours
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        if contours:
            largest = max(contours, key=cv2.contourArea)
            M = cv2.moments(largest)

            if M["m00"] != 0:
                cx = int(M["m10"] / M["m00"])
                cy = int(M["m01"] / M["m00"])

                # Translate to centered XY (Y axis inverted)
                X = cx - center_x
                Y = center_y - cy

                # Draw visuals
                cv2.circle(frame, (cx, cy), 10, (0, 255, 0), -1)
                cv2.putText(frame, f"({cx},{cy})", (cx + 10, cy),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
                cv2.circle(frame, (center_x, center_y), 5, (255, 0, 0), -1)
                cv2.arrowedLine(frame, (center_x, center_y), (cx, cy), (0, 255, 255), 2)
                cv2.putText(frame, f"X={X}, Y={Y}", (cx + 10, cy + 30),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 255), 2)

                # normalize coordinates to -1 to 1 range
                X_normalized = X / (width / 2) * 10
                Y_normalized = Y / (height / 2) * 10

                # # machinacommand = f"Move({X_normalized:.2f},{Y_normalized:.2f},0);"
                machinacommand = f"Move({-X_normalized:.2f},{-Y_normalized:.2f},0);"
                
                # if 1 second has passed, send command
                if (datetime.datetime.now() - current_time).total_seconds() > 1:
                    machina.send_command(machinacommand)
                    current_time = datetime.datetime.now()

                print(f"Centered XY coordinate: X={X}, Y={Y}")

        # Display
        cv2.imshow("Green Tracking - RealSense", frame)
        cv2.imshow("Mask", mask)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
finally:
    pipeline.stop()
    cv2.destroyAllWindows()