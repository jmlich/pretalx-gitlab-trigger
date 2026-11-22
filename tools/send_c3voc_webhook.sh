#!/bin/bash
# Sends the webhook that c3voc voctopublish sends after a recording upload, to test pretalx-peertube by hand.
#
# Usage: send_c3voc_webhook.sh PRETALX_URL EVENT_SLUG WEBHOOK_TOKEN SUBMISSION_ID VIDEO_URL
#   PRETALX_URL    e.g. http://localhost
#   WEBHOOK_TOKEN  shown on the event's Peertube settings page
#   SUBMISSION_ID  the "id" of a talk in schedule.json, list them with:
#                  curl -s PRETALX_URL/EVENT_SLUG/schedule/export/schedule.json \
#                    | jq -r '.schedule.conference.days[].rooms[][] | "\(.id) \(.code) \(.title)"'
#   VIDEO_URL      e.g. https://peertube.example.org/w/abc123

set -e
set -o pipefail

if [ "$#" -ne 5 ]; then
  sed -n '4,10p' "$0"
  exit 1
fi

PRETALX_URL=$1
EVENT_SLUG=$2
WEBHOOK_TOKEN=$3
SUBMISSION_ID=$4
VIDEO_URL=$5

payload=$(jq -n --arg event "${EVENT_SLUG}" --argjson id "${SUBMISSION_ID}" --arg video "${VIDEO_URL}" '
  {fahrplan: {conference: $event, id: $id}, peertube: {enabled: true, urls: [$video]}}
')

# pretalx-peertube answers 204 when it stored the link, 403 for a wrong token, 404 for an unknown talk
curl --silent --show-error --write-out 'HTTP %{http_code}\n' \
  --header "Authorization: ${WEBHOOK_TOKEN}" \
  --header 'Content-Type: application/json' \
  --data "${payload}" \
  "${PRETALX_URL}/${EVENT_SLUG}/p/peertube/c3voc/"
