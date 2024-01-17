import os
import shlex
import subprocess

import boto3

chunk_s3_location = ""
STATIC_ASSETS_BUCKET = "staticassets.goldcast.com"
output_directory = "downloads"


def download_file_from_s3(bucket_name, s3_file_key, local_file_name):
    s3 = boto3.client('s3')
    s3.download_file(bucket_name, s3_file_key, local_file_name)
    print(f"{local_file_name} has size: {os.path.getsize(local_file_name)}")
    return local_file_name


def download_files_from_s3(bucket_name, s3_folder, local_folder):
    s3 = boto3.client('s3')

    # List objects in the specified S3 folder
    response = s3.list_objects_v2(Bucket=bucket_name, Prefix=s3_folder)

    for obj in response.get('Contents', []):
        s3_file_key = obj['Key']
        local_file_name = os.path.join(local_folder, os.path.basename(s3_file_key))

        # Download each file
        s3.download_file(bucket_name, s3_file_key, local_file_name)
        print(f"{local_file_name} has size: {os.path.getsize(local_file_name)}")


def create_video_concat_command(input_files, output_file):
    num_files = len(input_files)
    filter_complex = "[0:v][0:a]"  # Start with inputs from the first file
    for i in range(1, num_files):
        filter_complex += f"[{i}:v][{i}:a]"  # Add inputs from subsequent files
    filter_complex += f"concat=n={num_files}:v=1:a=1[outv][outa]"

    num_files = len(input_files)

    command_string = "ffmpeg " + " ".join(["-i " + file for file in input_files]) + " " + \
                     f"-r 60 -filter_complex [0:v][0:a]{''.join(['[{}:v][{}:a]'.format(i, i) for i in range(1, num_files)])}concat=n={num_files}:v=1:a=1[outv][outa]" + " " + \
                     "-map [outv] -map [outa] -y " + output_file

    command = shlex.split(command_string)  # Split command string into arguments
    return command


def create_audio_merge_command(input_files, output_file):
    num_files = len(input_files)
    filter_complex = f"[0:a]"

    # Build the filter_complex string
    for i in range(1, num_files):
        filter_complex += f"[{i}:a]"

    filter_complex += f"amix=inputs={num_files}:duration=longest[outa]"

    # Construct the full FFmpeg command
    command_string = (
            "ffmpeg "
            + " ".join(["-i " + shlex.quote(file) for file in input_files])
            + " "
            + f"-filter_complex {filter_complex} -c:a libmp3lame -q:a 2 -map [outa] {shlex.quote(output_file)}"
    )

    command = shlex.split(command_string)
    return command


def copy_correct_m3u8_file_paths(member_id):
    local_m3u8_content = ""
    with open(f"downloads/local_{member_id}.m3u8", 'r') as m3u8_file:
        for line in m3u8_file:
            if line.strip().endswith(".ts"):
                line = os.path.join(output_directory, line.strip().split("/")[-1])
                line = line + "\n"
            local_m3u8_content += line

    # Write the modified content to a new m3u8 file
    with open(f"downloads/local_{member_id}.m3u8", 'w') as output_file:
        output_file.write(local_m3u8_content)


def copy_upload_content_to_hls(input_file, member_id, hls_time=3.9):
    downloads_directory = "downloads"
    os.makedirs(downloads_directory, exist_ok=True)
    cmd = [
        "ffmpeg", "-i", input_file, "-c", "copy", "-f", "hls", "-hls_time", str(hls_time),
        "-hls_playlist_type", "vod", "-hls_segment_filename", "downloads/segment_%03d.ts",
        f"downloads/local_{member_id}.m3u8"
    ]

    print(cmd)
    subprocess.run(cmd, check=True)

    copy_correct_m3u8_file_paths(member_id)


def concat_mp4_chunks(member_folder, sorted_start_times, member_id):
    output_file = f"combined_{member_id}.mp4"

    # input_files = [f"{member_id}_{start_time}.mp4" for start_time in sorted_start_times]

    input_files = [f"{member_id}/{member_id}_{index+1}.mp4" for index, start_time in enumerate(sorted_start_times)]

    cmd = create_video_concat_command(input_files, output_file)

    print(cmd)
    subprocess.run(cmd)
    copy_upload_content_to_hls(output_file, member_id, 4)

    local_mp3_file = os.path.join(os.getcwd(), f"output_{member_id}.mp3")
    audio_cmd = ["ffmpeg", "-i", output_file, local_mp3_file]
    subprocess.run(audio_cmd)

    return f"output_{member_id}.mp3"


def process_grouped_chunks(recording_session_id, chunk_metadata):
    audio_files = []
    for member_id, rows in chunk_metadata.items():
        print(f"Member ID: {member_id}")
        print(f"current dir: {os.getcwd()}")
        member_folder = os.path.join(os.getcwd(), member_id)
        os.makedirs(member_folder, exist_ok=True)

        s3_folder = 'your/s3/folder/prefix'

        # download_files_from_s3(STATIC_ASSETS_BUCKET, s3_folder, member_folder)

        start_times = [row.get("start_time") for row in rows]
        sorted_start_times = sorted(start_times)

        aud_file = concat_mp4_chunks(member_folder, sorted_start_times, member_id)
        audio_files.append(aud_file)

    aud_cmd = create_audio_merge_command(audio_files, "final_output.mp3")
    print(aud_cmd)
    subprocess.run(aud_cmd)



# if __name__ == "__main__":
#     input = {
#         "x1": [
#             {"id": "0a7d21a1-02e4-4e3d-9d4c-bda554f4e84a", "recording_session_id": "999", "member_id": "x1",
#              "start_time": "2024-01-16 11:31:53.480517"},
#             {"id": "2b82df60-79a9-48c4-aa19-9eb6e836a8c8", "recording_session_id": "999", "member_id": "x1",
#              "start_time": "2024-01-16 11:38:53.480517"}
#         ],
#         "x2": [
#             {"id": "4fb1d1f8-4bc5-468f-8085-9ea29cc2c66e", "recording_session_id": "999", "member_id": "x2",
#              "start_time": "2024-01-16 11:31:53.480517"},
#             {"id": "8b5e193a-8f04-4b06-a6c5-0ee3a9612cb6", "recording_session_id": "999", "member_id": "x2",
#              "start_time": "2024-01-16 11:3:53.480517"}
#         ]
#     }
#
#     process_grouped_chunks("abc", input)


# ffmpeg -i x1/x1_1.mp4 -i x1/x1_2.mp4 -r 30 -filter_complex "[0:v][0:a][1:v][1:a]concat=n=2:v=1:a=1[outv][outa]" -map "[outv]" -map "[outa]" -strict -2 -y combined_x1.mp4

# ffmpeg -i output_x1.mp3 -i output_x2.mp3 -filter_complex amix=inputs=2:duration=longest -c:a libmp3lame -q:a 2 output_g.mp3
# ['ffmpeg', '-i', 'output_x1.mp3', '-i', 'output_x2.mp3', '-filter_complex', '[0:a][1:a]amix=inputs=2:duration=longest[outa]', '-c:a', 'libmp3lame', '-q:a', '2', 'final_output.mp3']

# ffmpeg -i input1.mp3 -i input2.mp3 -filter_complex "[0:a][1:a]amix=inputs=2" -c:a libmp3lame -q:a 2 output.mp3
