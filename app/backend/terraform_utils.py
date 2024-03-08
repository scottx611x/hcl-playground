#!/usr/bin/env python3

import re
import os
import shutil
import subprocess
import sys
import uuid


def extract_locals_block(text):
    """
    Extracts the 'locals' block from a given HCL text and returns it along with the rest of the text.

    :param text: The HCL text containing a 'locals' block.
    :return: A tuple containing the 'locals' block content and the rest of the text.
    """
    start_pattern = re.compile(r'locals\s*{')
    start_match = start_pattern.search(text)

    if not start_match:
        return None, text  # No locals block found

    # Find the start of the locals block
    start_index = start_match.start()

    # Count braces to find the end of the locals block
    brace_count = 1
    i = start_match.end()
    while i < len(text) and brace_count > 0:
        if text[i] == '{':
            brace_count += 1
        elif text[i] == '}':
            brace_count -= 1
        i += 1

    # Extract the locals block and the rest of the text
    locals_block = text[start_index:i]
    rest_of_text = text[:start_index] + text[i:]

    rest_of_text = "\n".join(line for line in rest_of_text.splitlines() if not line.startswith("//"))

    return locals_block, rest_of_text


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

def handler(event) -> str:
    run_id = uuid.uuid4().hex

    os.mkdir(f"/scratch/{run_id}")

    # Copy .tfenv folder
    shutil.copytree('/home/root/.tfenv', '/scratch/.tfenv', dirs_exist_ok=True)

    # Parse the event data
    event_data = event

    # Log the event data
    print(f"EVENT_DATA: {event_data}", file=sys.stderr)

    # Extract elements from the event data
    body = event_data.get('body', '')
    print(f"BODY: {body}", file=sys.stderr)

    code = body.get('code', '') if body else ''
    print(f"CODE: {code}", file=sys.stderr)

    locals_block, code = extract_locals_block(code)

    print(f"LOCALS BLOCK: {locals_block}", file=sys.stderr)
    print(f"CODE: {code}", file=sys.stderr)

    path_parameters = event_data.get('pathParameters', '')
    print(f"PATH_PARAMETERS: {path_parameters}", file=sys.stderr)

    terraform_version = path_parameters.get('terraform_version', '') if path_parameters else ''
    print(f"TERRAFORM_VERSION: {terraform_version}", file=sys.stderr)

    if locals_block is not None:
        with open(f'/scratch/{run_id}/main.tf', 'a') as f:
            f.write(locals_block)

    # Set Terraform version with tfenv
    run_subprocess([
        '/scratch/.tfenv/bin/tfenv',
        'use', f"latest:^{terraform_version}"
    ], env={'BASHLOG_COLOURS': "0", 'TFENV_INSTALL_DIR': '/scratch/tfenv_installs'})

    terraform_path = f"/scratch/.tfenv/versions/{terraform_version}/terraform"

    # Format the Terraform configuration file
    run_subprocess([terraform_path, 'fmt', '-no-color', 'main.tf'], cwd=f'/scratch/{run_id}', check=False)

    # Initialize Terraform
    run_subprocess([terraform_path, 'init', '-no-color'], cwd=f'/scratch/{run_id}')

    # Execute Terraform console with the code from the event
    result = run_subprocess(
        [terraform_path, 'console'],
        input=code,
        cwd=f'/scratch/{run_id}',
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env={"TF_CLI_ARGS": "-no-color"}
    )

    shutil.rmtree(f'/scratch/{run_id}')

    return str(result.stdout) + str(result.stderr)