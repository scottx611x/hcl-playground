from functools import cache

from flask import Flask, render_template, request
from bs4 import BeautifulSoup
import requests

from backend.terraform_utils import handler

app = Flask(__name__)


@cache
def fetch_terraform_versions():
    url = "https://releases.hashicorp.com/terraform/"
    versions = []

    try:
        # Send a GET request to the URL
        response = requests.get(url)
        response.raise_for_status()  # Raise an error for bad responses

        # Parse the HTML content of the page
        soup = BeautifulSoup(response.text, 'html.parser')

        # Find all version links. Versions are typically in <a> tags within the main page content.
        # This might need adjustments if the page structure changes.
        for link in soup.find_all('a'):
            href = link.get('href')
            if href and 'terraform/' in href:
                version = href.rstrip('/').split("/")[-1]
                if version not in versions:  # Avoid duplicates
                    versions.append(version)

        return versions
    except requests.RequestException as e:
        print(f"An error occurred: {e}")
        return versions

# Route for serving the index page and handling form submission
@app.route('/', methods=['GET', 'POST'])
def index():
    output = ""
    if request.method == 'POST':
        # Extract code from the form submission
        code = request.form.get('codeInput').strip()
        version = request.form.get('terraformVersion')

        output = handler(
            {"pathParameters": {"terraform_version": version}, "body": {"code": code}},
        )

        return render_template('index.html', code=code, output=output, selected_terraform_version=version, terraform_versions=fetch_terraform_versions())

    return render_template('index.html', output=output, terraform_versions=fetch_terraform_versions())