# Handler function name must match the
# last part of <fileName>.<handlerName>
function handler () {

  # Get the data
  EVENT_DATA=$1

  # Log the event to stderr
  echo "EVENT_DATA: $EVENT_DATA" 1>&2;

  PAYLOAD=$(echo "$EVENT_DATA" | jq -r '.payload' | cat)

  # Update our main.tf with event data
  sed -i "s/\# DATA/${PAYLOAD}/" main.tf


  # Respond to Lambda service by echoing the received data back
#  RESPONSE="Echoing request: '$EVENT_DATA'"
#  echo $RESPONSE
#
#  terraform --version
  terraform fmt main.tf 1> /dev/null
  terraform init 1> /dev/null
  echo "local.a" | terraform console
}