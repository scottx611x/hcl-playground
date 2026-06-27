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
        cy.get('#runBtn', { timeout: 25000 }).should('not.be.disabled');
        cy.get('#output')
            .should('contain', '"az" = "us-east-1a"')
            .and('contain', '"cidr"');
    });

    it('also works with the OpenTofu engine', () => {
        cy.visit('/');
        cy.window().its('editor').should('exist');
        cy.get('.engine-btn[data-engine="tofu"]').click();
        cy.get('#runBtn').click();
        cy.get('#runBtn', { timeout: 25000 }).should('not.be.disabled');
        cy.get('#output').should('contain', '"az" = "us-east-1a"');
    });
});

describe('Every example evaluates without an error', () => {
    it('runs each example end to end', () => {
        cy.visit('/');
        cy.window().its('editor').should('exist');
        cy.get('#examplesBtn').click();
        cy.get('#examplesMenu button').its('length').then((n) => {
            for (let i = 0; i < n; i++) {
                cy.get('#examplesBtn').click();
                cy.get('#examplesMenu button').eq(i).click();
                cy.get('#runBtn').click();
                cy.get('#runBtn', { timeout: 25000 }).should('not.be.disabled');
                cy.get('#output').should('not.contain', 'Error');
            }
        });
    });
});

describe('Security: disallowed input is rejected', () => {
    it('rejects provider blocks via the API', () => {
        cy.request({
            method: 'POST',
            url: '/evaluate',
            failOnStatusCode: false,
            body: { engine: 'terraform', version: '1.15.7', code: 'provider "aws" {}' },
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
