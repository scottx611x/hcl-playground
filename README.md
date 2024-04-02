# hcl-playground
https://github.com/scottx611x/hcl-playground/assets/5629547/c434d740-2370-4d9b-bf64-52e0eda41b64

## Beta Site

https://development.hcl-playground.com/

## Description

HCL Playground App is an application designed to provide a playground/sandbox environment for evaluating HashiCorp Configuration Language (HCL) code on-demand.
The aim of this project is avoid the [toil/overhead required to simply evaluate some HCL-code](https://github.com/hashicorp/terraform/issues/24094#issuecomment-1825482867) where a user currently has to:
- Install terraform
- Setup a new project
- Write some HCL
- `terraform init`
- `terraform console`
- < test how [setproduct()](https://developer.hashicorp.com/terraform/language/functions/setproduct) works on your current `locals` data >
- "Oops I made a mistake!"
- `Ctrl+C`
- edit `locals` block
- `terraform console`
- rinse and repeat

If you've been in the depths of attempting to get "creative" with cobbling together the terraform functions available to massage some complex inputs you may catch my drift

## Getting Started

### Prerequisites

- Docker installed on your local machine
- Git (for cloning the repository)

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
   docker run -v /tmp:/scratch -it -p 8080:8080 hcl-playground
   ```
   Access the application at `http://localhost:8080`.

## CI/CD Pipeline (CircleCI)

The CI configuration is defined in `.circleci/config.yml`. The key jobs in the pipeline include:

1. **AWS Authentication (`aws-auth`)**:
   Obtains temporary AWS credentials via [CircleCI's OIDC pattern](https://circleci.com/docs/openid-connect-tokens/) for use in subsequent steps. This is necessary for actions like pushing Docker images to ECR and updating Kubernetes configurations.

2. **Push Docker Image (`push-image`)**:
   Builds the Docker image and pushes it to AWS ECR

3. **Deploy to EKS (`eks-deploy`)**:
   - Installs `kubectl` and `helm`.
   - Sets up Kubernetes configuration to be able to interact with the EKS cluster.
   - Applies Kubernetes deployment, service, and ingress manifests to the EKS cluster.
   - Verifies the deployment status.

4. **Run Tests (`test`)**:
   Pulls the Docker image built earlier in the pipeline from ECR and runs tests using Cypress.

5. **Setup Infrastructure (`setup-infra`)**:
   Uses Terraform to set up or update infrastructure as defined in the Terraform files located in the project.

### Workflow

The `build-deploy-dev` workflow orchestrates the above jobs:

- We start by setting up any required backing infrastructure using Terraform.
- Then we build and push the Docker image to ECR, runs tests against the image we just built, and if successful finally deploys to our EKS cluster
- The workflow is configured to run on pull requests only, excluding the `main` branch as development efforts are still in progress to get to a production-ready state

## Cypress-Based Tests

To run Cypress-based tests:

1. **Ensure Cypress is Installed**:
   If Cypress is not already installed, you can install it by running the following in the project root:
   ```bash
   npm install
   ```

2. **Run Cypress Tests**:
   Execute the Cypress tests using the Cypress UI:
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

## Authors

- **Scott Ouellette** - *Initial work* - [scottx611x](https://github.com/scottx611x)

## License

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details
