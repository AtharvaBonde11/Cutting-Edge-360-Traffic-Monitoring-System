import cv2
import os

def extract_frames(video_path, output_folder):
    # Create output folder if it doesn't exist
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    # Load the video
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print("Error: Could not open video.")
        return

    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    print(f"Total number of frames in the video: {frame_count}")

    count = 0
    while True:
        # Read a new frame
        ret, frame = cap.read()
        if not ret:
            break

        # Save the frame
        frame_filename = f"frame_{count:04d}.jpg"
        frame_path = os.path.join(output_folder, frame_filename)
        cv2.imwrite(frame_path, frame)
        print(f"Saved {frame_path}")

        count += 1

    # Release the video capture object
    cap.release()
    print("Released video resource.")

# Usage example
video_path = 'input/myvid_3.mp4'
output_folder = 'Frames/video_3'
extract_frames(video_path, output_folder)