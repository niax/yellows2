import { Stack, StackProps } from 'aws-cdk-lib';
import { Construct } from 'constructs';
import { DockerImageFunction, DockerImageCode } from 'aws-cdk-lib/aws-lambda';
import { LambdaRestApi, AccessLogFormat, LogGroupLogDestination, MethodLoggingLevel } from 'aws-cdk-lib/aws-apigateway';
import { LogGroup, RetentionDays } from 'aws-cdk-lib/aws-logs';
import { Distribution } from 'aws-cdk-lib/aws-cloudfront';
import { RestApiOrigin } from 'aws-cdk-lib/aws-cloudfront-origins';

export interface YellowsStackProps extends StackProps {
}

export class YellowsStack extends Stack {
  constructor(scope: Construct, id: string, props: YellowsStackProps) {
    super(scope, id, props);

    const apiLambda = new DockerImageFunction(this, 'BackendFunction', {
      code: DockerImageCode.fromImageAsset('./../backend/', {
        cmd: ["yellows.api_handler.lambda_handler"],
      }),
      logRetention: RetentionDays.FIVE_YEARS,
    });

    const accessLogGroup = new LogGroup(this, 'AccessLogGroup', {
      logGroupName: 'Yellows/ApiGateway/access.log',
      retention: RetentionDays.ONE_YEAR,
    });

    const apiGw = new LambdaRestApi(this, 'ApiGateway', {
      handler: apiLambda,
      deployOptions: {
        accessLogDestination: new LogGroupLogDestination(accessLogGroup),
        accessLogFormat: AccessLogFormat.jsonWithStandardFields(),
        loggingLevel: MethodLoggingLevel.INFO,
        tracingEnabled: true,
      },
    });

    const cloudfrontDistro = new Distribution(this, "CloudfrontDistro", {
      defaultBehavior: {
        origin: new RestApiOrigin(apiGw),
      },
    });
  }
}
