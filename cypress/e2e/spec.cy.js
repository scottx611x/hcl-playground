// Monaco throws benign internal errors when an automated browser inspects it;
// they don't affect the app, so don't fail the run on them.
Cypress.on('uncaught:exception', () => false);

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
        cy.get('.monaco-editor', { timeout: 20000 }).should('be.visible');
        cy.get('#runBtn').click();
        cy.get('#runBtn', { timeout: 25000 }).should('not.be.disabled');
        cy.get('#output')
            .should('contain', '"az" = "us-east-1a"')
            .and('contain', '"cidr"');
    });

    it('also works with the OpenTofu engine', () => {
        cy.visit('/');
        cy.get('.monaco-editor', { timeout: 20000 }).should('be.visible');
        cy.get('.engine-btn[data-engine="tofu"]').click();
        cy.get('#runBtn').click();
        cy.get('#runBtn', { timeout: 25000 }).should('not.be.disabled');
        cy.get('#output').should('contain', '"az" = "us-east-1a"');
    });
});

describe('Every example evaluates without an error', () => {
    it('runs each example end to end', () => {
        cy.visit('/');
        cy.get('.monaco-editor', { timeout: 20000 }).should('be.visible');
        // The menu's buttons exist even while hidden, so we can count without opening it.
        cy.get('#examplesMenu button').its('length').then((n) => {
            for (let i = 0; i < n; i++) {
                cy.get('#examplesBtn').click();             // open the menu fresh
                cy.get('#examplesMenu button').eq(i).click();  // select (this closes it)
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
