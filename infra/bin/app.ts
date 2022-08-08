#!/usr/bin/env node
import * as cdk from 'aws-cdk-lib';
import { YellowsStack } from '../lib/yellows-stack';

const app = new cdk.App();
new YellowsStack(app, 'YellowsStack', {
});
