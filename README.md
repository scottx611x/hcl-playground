# hcl-playground
<img src="./app/static/dog.png" height=100px  alt="Cute dog with HCL on its collar"/>

## Description

The HCL Playground App is a Dockerized Flask application designed to provide a playground environment for evaluating HashiCorp Configuration Language (HCL) code on-demand.
The aim of this project is avoid the

## Getting Started

### Prerequisites

- Docker installed on your local machine
- Git (for cloning the repository)
- Python and Flask (for local development without Docker)

### Local Development

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd hcl-playground
   ```

2. **Build the Docker image:**
   ```bash
   docker build -t hcl-playground .
   ```

3. **Run the Docker container:**
   ```bash
   docker run -v /tmp:/scratch -it -p 5000:8080 hcl-playground
   ```
   Access the application at `http://localhost:5000`.

## CI/CD Pipeline (CircleCI)

The CI configuration is defined in `.circleci/config.yml`. The key jobs in the pipeline include:

1. **AWS Authentication (`aws-auth`)**:
   Obtains temporary AWS credentials via [CircleCI's OIDC pattern](https://circleci.com/docs/openid-connect-tokens/) for use in subsequent steps. This is necessary for actions like pushing Docker images to ECR and updating Kubernetes configurations.

2. **Push Docker Image (`push-image`)**:
   Builds the Docker image and pushes it to AWS ECR. This step uses the `cimg/base:stable` Docker image as a base.

3. **Deploy to EKS (`eks-deploy`)**:
   - Installs `kubectl` and `helm`.
   - Sets up Kubernetes configuration to interact with the EKS cluster.
   - Applies Kubernetes deployment, service, and ingress manifests to the EKS cluster.
   - Verifies the deployment status.

4. **Run Tests (`test`)**:
   Pulls the Docker image built eariler in the pipeline from ECR and runs tests using Cypress.

5. **Setup Infrastructure (`setup-infra`)**:
   Uses Terraform to set up or update infrastructure as defined in the Terraform files located in the project.

### Workflow

The `build-deploy-dev` workflow orchestrates the above jobs:

- We start by setting up any required backing infrastructure using Terraform.
- Then we build and pushe the Docker image to ECR, runs tests against the image we just built, and if successful finally deploys to our EKS cluster
- The workflow is configured to run on pull requests only, excluding the `main` branch as development efforts are still in progress to get to a production-ready state

## Cypress-Based Tests

To run Cypress-based tests:

1. **Ensure Cypress is Installed**:
   If Cypress is not already installed, you can install it by running:
   ```bash
   npm install cypress
   ```

2. **Run Cypress Tests**:
   Execute the Cypress tests using the Cypress CLI:
   ```bash
   npx cypress open
   ```
   Or for headless testing:
   ```bash
   npx cypress run
   ```

   In the CI pipeline, Cypress tests are run as part of the `test` job using the Cypress CircleCI orb.

## Deployment

The application is deployed to AWS EKS using Kubernetes manifests. The deployment process is automated through the CircleCI pipeline, which builds the Docker image, pushes it to ECR, and then updates the Kubernetes deployment on EKS.

## Contributing

Please read [CONTRIBUTING.md](CONTRIBUTING.md) for details on our code of conduct, and the process for submitting pull requests to us.

## Authors

- **Scott Ouellette** - *Initial work* - [scottx611x](https://github.com/scottx611x)

## License

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details