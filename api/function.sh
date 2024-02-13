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
  echo "BODY: $BODY" 1>&2;

  DATA=$(echo "$BODY" | jq -r '.data' | cat)
  echo "DATA: $DATA" 1>&2;

  CODE=$(echo "$BODY" | jq -r '.code' | cat)
  echo "CODE: $CODE" 1>&2;

  PATH_PARAMETERS=$(echo "$EVENT_DATA" | jq -r '.pathParameters' | cat)
  echo "PATH_PARAMETERS: $PATH_PARAMETERS" 1>&2;

  TERRAFORM_VERSION=$(echo "$PATH_PARAMETERS" | jq -r '.terraform_version' | cat)
  echo "TERRAFORM_VERSION: $TERRAFORM_VERSION" 1>&2;

  # Note: this is going to get fucky w/ many invocations!
  cp main.tf /tmp/main.tf

  # Update our main.tf with event data
  if [ -n "$DATA" ]; then
    echo "$DATA" >> /tmp/main.tf
  fi

  # Set terraform version w/ tfenv
  BASHLOG_COLOURS=0 TFENV_INSTALL_DIR=/tmp/tfenv_installs /tmp/.tfenv/bin/tfenv use "latest:^$TERRAFORM_VERSION" 1>&2;

  TERRAFORM=/tmp/.tfenv/versions/"$TERRAFORM_VERSION"/terraform

  echo "main.tf:  $(cat /tmp/main.tf)" 1>&2;
  $TERRAFORM fmt -no-color /tmp/main.tf 1> /dev/null
  echo "main.tf formatted:  $(cat /tmp/main.tf)" 1>&2;

  cd /tmp || exit
  $TERRAFORM init -no-color 1> /dev/null

  export TERRAFORM=$TERRAFORM

  TF_CONSOLE_RESPONSE="$(echo $CODE | bash -c '$TERRAFORM console' 2>&1 | jq --slurp '-R' .)"
  echo "TF_CONSOLE_RESPONSE: $TF_CONSOLE_RESPONSE" 1>&2;

  RESPONSE="{\"statusCode\": 200, \"body\": $TF_CONSOLE_RESPONSE}"
  echo "$RESPONSE"
}