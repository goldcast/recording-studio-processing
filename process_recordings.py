import argparse
import asyncio
import enum
import json
import logging
import os
import subprocess
import sys
from time import sleep

import boto3

from process_chunks import process_grouped_chunks
from ves_utils import get_chunks_metadata

logger = logging.getLogger(__name__)

VIDEO_TRANSLATION_BUCKET = "goldcast-video-translation"
VIDEO_ARCHIVE_BUCKET = "goldcast-video-archive"
GCP_BUCKET = "dubbing_in"
GCP_PROJECT_ID = "goldcast"

secrets_manager = boto3.client("secretsmanager")

DJANGO_ADMIN_TOKEN = json.loads(
    secrets_manager.get_secret_value(SecretId="prod/admin-token")["SecretString"]
)["token"]
DJANGO_ENDPOINT = "https://backend.goldcast.io"

# VES :- Video Editing Server
VES_TOKEN = secrets_manager.get_secret_value(SecretId="prod/content-lab-credentials")[
    "SecretString"
]

mediastore_endpoint = (
        "https://uago73t2my3lb2.data.mediastore.us-east-1.amazonaws.com"
    )

# chunks_location_s3 : ""




if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--event_id", type=str, required=True)
    parser.add_argument("--broadcast_id", type=str, required=True)
    parser.add_argument("--recording_session_id", type=str, required=True)
    parser.add_argument("--env", type=str, default="prod")

    args = parser.parse_args()
    event_id = args.event_id
    broadcast_id = args.broadcast_id
    recording_session_id = args.recording_session_id
    env = args.env

    chunks_meta = get_chunks_metadata(recording_session_id, VES_TOKEN)

    process_grouped_chunks(recording_session_id, chunks_meta)

    # TODO
    # PRE-Processing
    # 1. when recording ends -> create an entry into custom-upload.
    # 2. instead of batch-transcription trigger -> recording-studio-processing.
    # PROCESSING
    # 1. fetch chunks metadata for a recording id.
    # 2. group chunks by member ids.
    # 3. sort each group by start time.
    # 4. for each member chunks
        # - download each chunks from s3.
        # - combine the chunks to composite mp4.
        # - upload composite mp4 to s3.
        # - convert each mp4 to hls and upload to s3.
    # 5. convert each mp4 to mp3.
    # 6. merge all the mp3 and upload to filestack s3.
    # 7. trigger batch-transcription for custom upload (AUDIO). - composite mp3
    # 8. Do the FE handling to read individual streams for speaker grid.
    # Note : all the s3 location needs to be properly placed.
