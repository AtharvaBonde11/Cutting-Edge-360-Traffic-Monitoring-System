import open3d as o3d
import numpy as np
import cv2
import os
import gc
from concurrent.futures import ThreadPoolExecutor

# Function to load a point cloud from a file
def load_point_cloud(file_path):
    try:
        return o3d.io.read_point_cloud(file_path)
    except Exception as e:
        print(f"Failed to load point cloud from {file_path}: {e}")
        return None

# Downsample the point cloud to increase processing speed
def downsample_point_cloud(pcd, voxel_size=0.1):  # Increased voxel size
    return pcd.voxel_down_sample(voxel_size)

# Function to align point clouds using the ICP algorithm
def align_point_clouds(source, target, threshold=0.1, max_iterations=50):  # Increased max_iterations
    source.estimate_normals(search_param=o3d.geometry.KDTreeSearchParamHybrid(radius=0.1, max_nn=30))
    target.estimate_normals(search_param=o3d.geometry.KDTreeSearchParamHybrid(radius=0.1, max_nn=30))
    result = o3d.pipelines.registration.registration_icp(
        source, target, threshold, np.eye(4),
        o3d.pipelines.registration.TransformationEstimationPointToPlane(),
        o3d.pipelines.registration.ICPConvergenceCriteria(relative_fitness=1e-6, relative_rmse=1e-6, max_iteration=max_iterations)
    )
    return result.transformation

# Function to transform an image
def transform_image(img, transformation, intrinsics):
    h, w = img.shape[:2]
    # Create a 3x3 transformation matrix for use with cv2.warpPerspective
    transformation_cv2 = np.zeros((3, 3), dtype=np.float32)
    transformation_cv2[:2, :] = transformation[:2, :3]  # Take only the 2x3 part of the 3x4 matrix
    transformation_cv2[2, :] = [0, 0, 1]  # Set the third row
    # Apply transformation to the entire image
    transformed_img = cv2.warpPerspective(img, transformation_cv2, (w, h))
    return transformed_img

# Function to stitch images using CPU to avoid OpenCL errors
def stitch_images_cpu(images):
    cv2.ocl.setUseOpenCL(False)  # Disable OpenCL
    stitcher = cv2.Stitcher_create(cv2.Stitcher_PANORAMA)
    stitcher.setPanoConfidenceThresh(0.5)
    stitcher.setWaveCorrection(True)
    status, pano = stitcher.stitch(images)
    if status != cv2.Stitcher_OK:
        print(f"Stitching failed: {status}")
        return None
    return pano

# Load camera intrinsics (modify as per your camera)
camera_intrinsics = o3d.camera.PinholeCameraIntrinsic()
camera_intrinsics.set_intrinsics(width=1920, height=1080, fx=1000, fy=1000, cx=960, cy=540)

# Load and align point clouds
pcd_files = ['video_output_point_cloud/myvid_1/', 'video_output_point_cloud/myvid_2/', 'video_output_point_cloud/myvid_3/']
video_dirs = ['Frames/video_1/', 'Frames/video_2/', 'Frames/video_3/']
panorama_output_dir = 'Panorama/'
transformed_output_dir = 'Transformed_images/'

os.makedirs(panorama_output_dir, exist_ok=True)
os.makedirs(transformed_output_dir, exist_ok=True)

total_frames = 250  # Assuming there are 250 frames for each video

def process_frame(i):
    try:
        # Load and downsample point clouds
        point_clouds = [downsample_point_cloud(load_point_cloud(os.path.join(pcd_file, f'frame_{i}.pcd'))) for pcd_file in pcd_files]
        point_clouds = [pcd for pcd in point_clouds if pcd is not None]

        if len(point_clouds) < 2:
            print(f"Insufficient point clouds for alignment in frame {i}")
            return

        base_pcd = point_clouds[0]
        transformations = [np.eye(4)]  # Identity for the first frame

        for j in range(1, len(point_clouds)):
            trans = align_point_clouds(point_clouds[j], base_pcd, threshold=0.1, max_iterations=50)  # Increased max_iterations
            transformations.append(trans)
            point_clouds[j].transform(trans)
            base_pcd += point_clouds[j]  # Add transformed point cloud to base

        # Transform images using aligned point clouds
        transformed_images = []
        for k, video_dir in enumerate(video_dirs):
            img_path = os.path.join(video_dir, f'frame_{i:04d}.jpg')
            img = cv2.imread(img_path)

            if img is None:
                print(f"Failed to read image {img_path}")
                continue

            # Further resize image for faster processing
            img = cv2.resize(img, (640, 360))  # Further resized image

            transformed_img = transform_image(img, transformations[k], camera_intrinsics)
            transformed_images.append(transformed_img)

            # Save intermediate transformed image for debugging
            debug_img_path = os.path.join(transformed_output_dir, f'transformed_frame_{i:04d}_video{k}.jpg')
            cv2.imwrite(debug_img_path, transformed_img)
            print(f"Transformed image saved to {debug_img_path}")

        if len(transformed_images) < 2:
            print(f"Insufficient transformed images for stitching in frame {i}")
            return

        # Stitch images together using CPU
        panorama = stitch_images_cpu(transformed_images)

        if panorama is not None:
            output_path = os.path.join(panorama_output_dir, f'panorama_frame_{i:04d}.jpg')
            cv2.imwrite(output_path, panorama)
            print(f"Panorama image saved to {output_path}")

        # Clean up to free memory
        del point_clouds
        del transformations
        del transformed_images
        gc.collect()  # Force garbage collection

    except Exception as e:
        print(f"Error processing frame {i}: {e}")

# Process frames sequentially to manage memory usage better
for i in range(total_frames):
    process_frame(i)

# Finished processing all frames
print("All frames processed successfully")