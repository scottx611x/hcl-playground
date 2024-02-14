#!/usr/bin/env python3

import json
import os
import shutil
import subprocess
import sys
import uuid


def run_subprocess(command, **kwargs):
    _kwargs = dict(check=True, shell=True, stdout=sys.stderr, stderr=sys.stderr, text=True)
    _kwargs.update(kwargs)

    try:
        # Execute the command, capture stdout and stderr
        result = subprocess.run(" ".join(command), **_kwargs)

        # Print the standard output of the command
        if result.stdout:
            print("Output:", result.stderr, file=sys.stdout)

        # Print the standard error of the command, if any
        if result.stderr:
            print("Errors:", result.stderr, file=sys.stderr)

    except subprocess.CalledProcessError as e:
        # If the command failed, print the error and exit
        print(f"Command failed with error code {e.returncode}:", e.stderr, file=sys.stderr)
        raise e  # Optionally re-raise the exception if you want calling code to handle it

    return result

def handler(event, context):
    run_id = uuid.uuid4().hex

    os.mkdir(f"/tmp/{run_id}")

    # Copy .tfenv folder
    shutil.copytree('/home/root/.tfenv', '/tmp/.tfenv', dirs_exist_ok=True)

    # Parse the event data
    event_data = json.loads(event)

    # Log the event data
    print(f"EVENT_DATA: {event_data}", file=sys.stderr)

    # Extract elements from the event data
    body = event_data.get('body', '')
    print(f"BODY: {body}", file=sys.stderr)

    data = body.get('data', '') if body else ''
    print(f"DATA: {data}", file=sys.stderr)

    code = body.get('code', '') if body else ''
    print(f"CODE: {code}", file=sys.stderr)

    path_parameters = event_data.get('pathParameters', '')
    print(f"PATH_PARAMETERS: {path_parameters}", file=sys.stderr)

    terraform_version = path_parameters.get('terraform_version', '') if path_parameters else ''
    print(f"TERRAFORM_VERSION: {terraform_version}", file=sys.stderr)

    # Update /tmp/main.tf with event data
    if data:
        with open(f'/tmp/{run_id}/main.tf', 'a') as f:
            f.write(data)

    # Set Terraform version with tfenv
    run_subprocess([
        '/tmp/.tfenv/bin/tfenv',
        'use', f"latest:^{terraform_version}"
    ], env={'BASHLOG_COLOURS': "0", 'TFENV_INSTALL_DIR': '/tmp/tfenv_installs'})

    terraform_path = f"/tmp/.tfenv/versions/{terraform_version}/terraform"

    # Format the Terraform configuration file
    run_subprocess([terraform_path, 'fmt', '-no-color', '/tmp/main.tf'], cwd=f'/tmp/{run_id}', check=False)

    # Initialize Terraform
    run_subprocess([terraform_path, 'init', '-no-color'], cwd=f'/tmp/{run_id}')

    # Execute Terraform console with the code from the event
    run_subprocess(
        [terraform_path, 'console'],
        input=code,
        cwd=f'/tmp/{run_id}',
        check=False,
        stdout=sys.stdout,
        stderr=sys.stdout,
        env={"TF_CLI_ARGS": "-no-color"}
    )

    shutil.rmtree(f'/tmp/{run_id}')


if __name__ == "__main__":
    event = sys.argv[1]
    context = sys.argv[1]
    handler(event, context)