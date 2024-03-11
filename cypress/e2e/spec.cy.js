describe('Ensure that HCL Playground loads', () => {
    it('Visits the initial project page', () => {
        cy.visit('/');
        cy.contains('HCL Playground');
    });
});

describe('Ensure that the base example produces the expected output when evalutated', () => {
    it('Submits an HCL Playground sample', () => {
        cy.visit('/');
        cy.get('#evalutate').click()
        cy.get('#outputSection', { timeout: 10000 }).should('be.visible');
        cy.get('#output').contains(`[
  {
    "availability_zone" = "us-east-1a"
    "cidr_block" = "10.0.0.0.0/16.0/24"
    "region" = "us-east-1"
  },
  {
    "availability_zone" = "us-east-1b"
    "cidr_block" = "10.0.1.0.0/16.0/24"
    "region" = "us-east-1"
  },
  {
    "availability_zone" = "us-west-2a"
    "cidr_block" = "10.0.2.0.0/16.0/24"
    "region" = "us-west-2"
  },
  {
    "availability_zone" = "us-west-2b"
    "cidr_block" = "10.0.3.0.0/16.0/24"
    "region" = "us-west-2"
  },
  {
    "availability_zone" = "eu-central-1a"
    "cidr_block" = "10.0.4.0.0/16.0/24"
    "region" = "eu-central-1"
  },
  {
    "availability_zone" = "eu-central-1b"
    "cidr_block" = "10.0.5.0.0/16.0/24"
    "region" = "eu-central-1"
  },
]`);
    });
});