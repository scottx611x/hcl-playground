describe('HCL Playground loads', () => {
    it('shows the app', () => {
        cy.visit('/');
        cy.contains('HCL Playground');
    });
});

describe('Healthcheck', () => {
    it('is accessible', () => {
        cy.request('/health').its('body').should('contain', 'healthy');
    });
});

describe('Evaluating the default example', () => {
    it('returns the expected expression output (Terraform)', () => {
        cy.visit('/');
        cy.window().its('editor').should('exist');   // wait for Monaco
        cy.get('#runBtn').click();
        cy.get('#output', { timeout: 20000 })
            .should('contain', '"region" = "us-east-1"')
            .and('contain', '"availability_zone" = "us-east-1a"');
    });

    it('also works with the OpenTofu engine', () => {
        cy.visit('/');
        cy.window().its('editor').should('exist');
        cy.get('.engine-btn[data-engine="tofu"]').click();
        cy.get('#runBtn').click();
        cy.get('#output', { timeout: 20000 })
            .should('contain', '"region" = "us-east-1"');
    });
});

describe('Security: disallowed input is rejected', () => {
    it('rejects provider blocks via the API', () => {
        cy.request({
            method: 'POST',
            url: '/evaluate',
            failOnStatusCode: false,
            body: { engine: 'terraform', version: '1.9.8', code: 'provider "aws" {}' },
        }).then((resp) => {
            expect(resp.status).to.eq(400);
            expect(resp.body.error).to.contain('Only');
        });
    });

    it('rejects an injection attempt in the version field', () => {
        cy.request({
            method: 'POST',
            url: '/evaluate',
            failOnStatusCode: false,
            body: { engine: 'terraform', version: '1.0.0; id', code: 'upper("hi")' },
        }).then((resp) => {
            expect(resp.status).to.eq(400);
        });
    });
});
