#!/usr/bin/env node
import * as cdk from 'aws-cdk-lib';
import { YellowsStack } from '../lib/yellows-stack';
import { CertificateStack } from '../lib/cert-stack';

const app = new cdk.App();
// TODO: make this a parameter?
const domainName = 'yellows2.niax.uk';

const certStack = new CertificateStack(app, 'CertificateStack', {
  domainName: domainName,
  env: {
    region: "us-east-1",
  }
});

new YellowsStack(app, 'YellowsStack', {
  domainName: domainName,
  certificateArn: 'arn:aws:acm:us-east-1:778925373815:certificate/f1ca31b9-89c9-4c99-8a97-56f3cba7c800',
});
