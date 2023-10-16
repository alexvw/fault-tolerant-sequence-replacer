import os
import argparse
import time
import glob

def path(string):
    return string.replace("/", os.sep)

def run_command(command):
    print(f"Running command: {command}")
    return os.popen(command).read()

def replace_frames_with_images(video_path, image_dir):
    # Step 1: Extract fps
    print("Extracting FPS from video...")
    output = run_command(f'ffprobe -v error -select_streams v -of default=noprint_wrappers=1:nokey=1 -show_entries stream=r_frame_rate "{video_path}"')
    fps = int(output.split("/")[0]) // int(output.split("/")[1].strip())
    print(f"Extracted FPS: {fps}")

    # Step 2: Extract duration
    print("Extracting duration from video...")
    output = run_command(f'ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "{video_path}"')
    duration = int(float(output.strip()))
    print(f"Extracted duration: {duration}s")

    # Get the number of replacement frames
    num_replacements = len(glob.glob(path(f"{image_dir}{os.sep}*.jpg")))

    # Step 3: Extract audio
    print("Extracting audio from video...")
    run_command(f'ffmpeg -i "{video_path}" -vn -acodec copy "{image_dir}{os.sep}audio.aac" -y -loglevel error')

    # Create chunks
    chunk_size = 1000
    chunks = [(i * chunk_size + 1, (i + 1) * chunk_size) for i in range(int(fps) * duration // chunk_size)]
    if int(fps) * duration % chunk_size != 0:
        chunks.append(((len(chunks) * chunk_size) + 1, int(fps) * duration))

    chunk_videos = []
    start_chunk = 0
    for i, (start_frame, end_frame) in enumerate(chunks):
        chunk_video = path(f"{image_dir}{os.sep}chunk_{start_frame}_{end_frame}.mp4")
        if os.path.isfile(chunk_video):
            start_chunk = i
            chunk_videos.append(chunk_video)

    start_time = time.time()
    # Step 4: Process each chunk
    for i, (start_frame, end_frame) in enumerate(chunks[start_chunk:], start=start_chunk):
        print(f"Processing chunk {i + 1} out of {len(chunks)}...")
        with open(path(f"{image_dir}{os.sep}frames.txt"), "w") as file:
            for frame_number in range(start_frame, min(end_frame + 1, num_replacements + 1)):
                frame_path = path(f"{image_dir}{os.sep}{frame_number:04d}.jpg")
                file.write(f"file '{frame_path}'\n")
                file.write(f"duration {1 / fps}\n")
        chunk_video = path(f"{image_dir}{os.sep}chunk_{start_frame}_{end_frame}.mp4")
        run_command(f'ffmpeg -f concat -safe 0 -i "{image_dir}{os.sep}frames.txt" -c:v libx264 -r {fps} -pix_fmt yuv420p -y "{chunk_video}" -loglevel error')
        chunk_videos.append(chunk_video)
        elapsed_time = time.time() - start_time
        remaining_chunks = len(chunks) - (i + 1)
        estimated_remaining_time = (elapsed_time / (i + 1)) * remaining_chunks
        print(f"Finished processing chunk {i + 1}. Estimated time remaining: {estimated_remaining_time / 60:.2f} minutes")

    # Step 5: Concatenate all chunks
    print("Concatenating all chunks...")
    with open(path(f"{image_dir}{os.sep}videos.txt"), "w") as file:
        for chunk_video in chunk_videos:
            file.write(f"file '{chunk_video}'\n")
    run_command(f'ffmpeg -f concat -safe 0 -i "{image_dir}{os.sep}videos.txt" -c copy "{image_dir}{os.sep}output_no_audio.mp4" -y -loglevel error')

    # Step 6: Add audio
    print("Adding audio to the video...")
    run_command(f'ffmpeg -i "{image_dir}{os.sep}output_no_audio.mp4" -i "{image_dir}{os.sep}audio.aac" -c copy "{image_dir}{os.sep}output.mp4" -y -loglevel error')

    # Step 7: Cleanup
    print("Cleaning up intermediary files...")
    for chunk_video in chunk_videos:
        if os.path.exists(chunk_video):
            os.remove(chunk_video)
    if os.path.exists(path(f"{image_dir}{os.sep}audio.aac")):
        os.remove(path(f"{image_dir}{os.sep}audio.aac"))
    if os.path.exists(path(f"{image_dir}{os.sep}output_no_audio.mp4")):
        os.remove(path(f"{image_dir}{os.sep}output_no_audio.mp4"))
    print("Cleanup done!")

if __name__ == "__main__":
    print("Running script...")
    parser = argparse.ArgumentParser(description='Replace video frames with images.')
    parser.add_argument('video', type=str, help='Path to the video file.')
    args = parser.parse_args()

    replace_frames_with_images(args.video, '.')
