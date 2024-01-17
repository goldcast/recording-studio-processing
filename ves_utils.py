import json
import logging

import requests
from tenacity import retry, stop_after_attempt

logger = logging.getLogger(__name__)


@retry(
    reraise=True,
    stop=stop_after_attempt(2),
)
def set_status_for_transcription(broadcast_id, status, video_editing_token, uploaded_asset=False, env="prod"):
    # A list because this will patch both the alpha and prod once prod is deployed
    video_editing_servers = [
        "https://contentlab.alpha.goldcast.io",
        "https://contentlab.goldcast.io",
    ]

    if uploaded_asset:
        if env == "prod":
            video_editing_servers = ["https://contentlab.goldcast.io", ]
        else:
            video_editing_servers = ["https://contentlab.alpha.goldcast.io", ]

    payload = {"batch_transcription_status": status}
    for video_editing_server in video_editing_servers:
        try:
            video_resp = requests.post(
                f"{video_editing_server}/cron/transcription/{broadcast_id}/job_status/",
                json=payload,
                headers={"Authorization": video_editing_token},
            )
            video_resp.raise_for_status()
        except Exception as e:
            """
            We don't need to raise an exception and fail the task when the patch fails.
            """
            logger.exception(
                f"Failed to set status for: {broadcast_id} on: {video_editing_server}", exc_info=True,
            )


@retry(
    reraise=True,
    stop=stop_after_attempt(2),
)
def get_chunks_metadata(recording_session_id, video_editing_token, env="prod"):
    video_editing_servers = [
        "https://contentlab.alpha.goldcast.io",
        "https://contentlab.goldcast.io",
    ]

    for video_editing_server in video_editing_servers:
        try:
            video_resp = requests.get(
                f"{video_editing_server}/recording_sessions/{recording_session_id}/chunks/",
                headers={"Authorization": video_editing_token},
            )

            if video_resp.status_code == 200:
                # Parse the JSON response
                response_json = video_resp.json()

                # Create a dictionary to store grouped rows by 'member_id'
                grouped_response = {}

                # Group rows by 'member_id'
                for row in response_json:
                    member_id = row["member_id"]
                    if member_id not in grouped_response:
                        grouped_response[member_id] = []
                    grouped_response[member_id].append(row)

                # Now, 'grouped_response' is a dictionary where keys are 'member_id' and values are lists of corresponding rows
                for member_id, rows in grouped_response.items():
                    print(f"Member ID: {member_id}")
                    for row in rows:
                        print(row)

                return grouped_response
            else:
                print(f"Error: {video_resp.status_code}")

        except Exception as e:
            """
            We don't need to raise an exception and fail the task when the patch fails.
            """
            logger.exception(
                f"Failed to get chunks for: {recording_session_id} on: {video_editing_server}", exc_info=True,
            )


