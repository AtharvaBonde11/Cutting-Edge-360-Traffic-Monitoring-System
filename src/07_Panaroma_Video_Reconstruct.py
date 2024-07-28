import cv2
import os

# Directory containing the frames
frame_dir = './Panorama Obtained'
# Output video file name
output_video = './Panaroma_Video/Panaroma_video_try.mp4'

# Desired video properties
fps = 30  # Frames per second
target_width = 3840
target_height = 2160

# Get a sorted list of all frame files
frame_files = sorted([f for f in os.listdir(frame_dir) if f.startswith('panorama_frame_') and f.endswith('.jpg')])

if not frame_files:
    print("No frames found in the directory.")
    exit()

# Read the first frame to ensure the path is correct
first_frame_path = os.path.join(frame_dir, frame_files[0])
first_frame = cv2.imread(first_frame_path)

if first_frame is None:
    print(f"Failed to read the first frame: {first_frame_path}")
    exit()

print(f"Original frame dimensions: {first_frame.shape[1]}x{first_frame.shape[0]}")
print(f"Target frame dimensions: {target_width}x{target_height}")

# Initialize the video writer
fourcc = cv2.VideoWriter_fourcc(*'mp4v')
video_writer = cv2.VideoWriter(output_video, fourcc, fps, (target_width, target_height))

if not video_writer.isOpened():
    print(f"Video writer could not be opened. Check codec and file path: {output_video}")
    exit()

# Iterate through the frame files and add them to the video
for frame_file in frame_files:
    frame_path = os.path.join(frame_dir, frame_file)
    frame = cv2.imread(frame_path)

    if frame is None:
        print(f"Skipping file, could not read: {frame_path}")
        continue

    # Resize frame to the target dimensions
    resized_frame = cv2.resize(frame, (target_width, target_height), interpolation=cv2.INTER_LINEAR)

    video_writer.write(resized_frame)
    print(f"Added frame to video: {frame_path}")

# Release the video writer
video_writer.release()
print(f"Video saved as {output_video}")