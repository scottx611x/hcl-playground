# Handler function name must match the
# last part of <fileName>.<handlerName>
function handler () {

  # Get the data
  EVENT_DATA=$1

  # Log the event to stderr
  echo "EVENT_DATA: $EVENT_DATA" 1>&2;

  PAYLOAD=$(echo "$EVENT_DATA" | jq -r '.payload' | cat)

  # Note: this is going to get fucky w/ many invocations!
  cp main.tf /tmp/main.tf.bak
  cp main.tf /tmp/main.tf

  # Update our main.tf with event data
  sed -i "s/\# DATA/${PAYLOAD}/" /tmp/main.tf

  # Respond to Lambda service by echoing the received data back
  RESPONSE="Echoing request: '$EVENT_DATA'"
  echo "$RESPONSE"

  terraform --version
  terraform fmt /tmp/main.tf 1> /dev/null
  pushd /tmp || exit
  terraform init 1> /dev/null
  echo "local.a" | terraform console
  popd
}