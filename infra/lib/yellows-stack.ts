import { Stack, StackProps } from 'aws-cdk-lib';
import { Construct } from 'constructs';

export interface YellowsStackProps extends StackProps {
}

export class YellowsStack extends Stack {
  constructor(scope: Construct, id: string, props: YellowsStackProps) {
    super(scope, id, props);
  }
}
