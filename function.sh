# Handler function name must match the
# last part of <fileName>.<handlerName>
function handler () {
  cp -r /home/root/.tfenv /tmp/.tfenv

  # Get the data
  EVENT_DATA=$1

  # Log the event to stderr
  echo "EVENT_DATA: $EVENT_DATA" 1>&2;

  # Handles for lambda testing and API Gateway testing
  BODY=$(echo "$EVENT_DATA" | jq -r '.body' | cat)
  PAYLOAD=$(echo "$BODY" | jq -r '.payload' | cat)
  PATH_PARAMETERS=$(echo "$EVENT_DATA" | jq -r '.pathParameters' | cat)
  TERRAFORM_VERSION=$(echo "$PATH_PARAMETERS" | jq -r '.terraform_version' | cat)

  echo "PAYLOAD: $PAYLOAD" 1>&2;
  echo "TERRAFORM_VERSION: $TERRAFORM_VERSION" 1>&2;

  # Note: this is going to get fucky w/ many invocations!
  cp main.tf /tmp/main.tf

  # Update our main.tf with event data
  sed -i "s/DATA/${PAYLOAD}/" /tmp/main.tf

  # Set terraform version w/ tfenv
  BASHLOG_COLOURS=0 TFENV_INSTALL_DIR=/tmp/tfenv_installs /tmp/.tfenv/bin/tfenv use "latest:^$TERRAFORM_VERSION" 1>&2;

  TERRAFORM=/tmp/.tfenv/versions/"$TERRAFORM_VERSION"/terraform

  echo "main.tf:  $(cat /tmp/main.tf)" 1>&2;
  $TERRAFORM fmt -no-color /tmp/main.tf 1> /dev/null
  echo "main.tf formatted:  $(cat /tmp/main.tf)" 1>&2;

  cd /tmp || exit
  $TERRAFORM init -no-color 1> /dev/null

  TF_CONSOLE_RESPONSE="$(echo "local.test" | $TERRAFORM console | jq --slurp '-R' .)"
  echo "TF_CONSOLE_RESPONSE: $TF_CONSOLE_RESPONSE" 1>&2;

  RESPONSE="{\"statusCode\": 200, \"body\": $TF_CONSOLE_RESPONSE}"
  echo "$RESPONSE"
}