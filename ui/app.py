from flask import Flask, render_template, request
from bs4 import BeautifulSoup
import requests

app = Flask(__name__)


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
        data = request.form.get('dataInput').strip()
        code = request.form.get('codeInput').strip()
        version = request.form.get('terraformVersion')

        response = requests.post(
            "http://localhost:9000/2015-03-31/functions/function/invocations",
            json={"pathParameters": {"terraform_version": version}, "body": {"code": code, "data": f"\n{data}"}}

        )

        if not response.text:
            output = response.json()["body"]
        else:
            output = response.text
        return render_template('index.html', data=data, code=code, output=output, selected_terraform_version=version, terraform_versions=fetch_terraform_versions())

    return render_template('index.html', output=output, terraform_versions=fetch_terraform_versions())


if __name__ == '__main__':
    app.run(debug=True)