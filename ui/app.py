from flask import Flask, render_template, request
import requests

app = Flask(__name__)


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

        if response.ok:
            output = response.json()["body"]
        else:
            output = response.text

    return render_template('index.html', output=output)


if __name__ == '__main__':
    app.run(debug=True)