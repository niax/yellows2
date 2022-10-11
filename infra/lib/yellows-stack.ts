import { Stack, StackProps, Duration, CfnParameter, SecretValue } from 'aws-cdk-lib';
import { Construct } from 'constructs';
import { DockerImageFunction, DockerImageCode, IFunction, Tracing } from 'aws-cdk-lib/aws-lambda';
import { LambdaRestApi, AccessLogFormat, LogGroupLogDestination, MethodLoggingLevel, RestApi } from 'aws-cdk-lib/aws-apigateway';
import { LogGroup, RetentionDays } from 'aws-cdk-lib/aws-logs';
import { Distribution, PriceClass, SecurityPolicyProtocol, OriginRequestPolicy, CachePolicy, ViewerProtocolPolicy, AllowedMethods, OriginRequestHeaderBehavior, OriginAccessIdentity, OriginRequestCookieBehavior, OriginRequestQueryStringBehavior, IDistribution } from 'aws-cdk-lib/aws-cloudfront';
import { RestApiOrigin, S3Origin } from 'aws-cdk-lib/aws-cloudfront-origins';
import { Bucket, BucketEncryption, IBucket } from 'aws-cdk-lib/aws-s3';
import { BucketDeployment, Source } from 'aws-cdk-lib/aws-s3-deployment';
import { ISecret, Secret } from 'aws-cdk-lib/aws-secretsmanager';
import { ITable, Table, AttributeType, BillingMode } from 'aws-cdk-lib/aws-dynamodb';
import { ARecord, AaaaRecord, HostedZone, RecordTarget } from 'aws-cdk-lib/aws-route53';
import { CloudFrontTarget } from 'aws-cdk-lib/aws-route53-targets';
import { Certificate, ICertificate } from 'aws-cdk-lib/aws-certificatemanager';

export interface YellowsStackProps extends StackProps {
  domainName: string,
  certificateArn: string,
}

export class YellowsStack extends Stack {
  constructor(scope: Construct, id: string, props: YellowsStackProps) {
    super(scope, id, props);

    const dataTable = this.makeDataTable();
    const apiLambda = this.makeBackendFunction(dataTable, props.domainName);
    const apiGw = this.makeApiGateway(apiLambda);
    const staticBucket = this.makeStaticContent();

    const certificate = Certificate.fromCertificateArn(this, 'CloudfrontCert', props.certificateArn);
    const cloudfrontDistro = this.makeCloudfrontDistribution(staticBucket, apiGw, certificate, [props.domainName]);

    this.makeDnsRecords(cloudfrontDistro, props.domainName);
    this.exportValue(cloudfrontDistro.distributionDomainName);
  }

  private makeDataTable(): ITable {
    const table = new Table(this, 'DataTable', {
      partitionKey: { name: 'PK', type: AttributeType.STRING },
      sortKey: { name: 'SK', type: AttributeType.STRING },
      billingMode: BillingMode.PAY_PER_REQUEST,
      timeToLiveAttribute: 'TimeToLive',
    });
    table.addGlobalSecondaryIndex({
      partitionKey: { name: 'SK', type: AttributeType.STRING },
      sortKey: { name: 'PK', type: AttributeType.STRING },
      indexName: 'InvertedIndex',
    });
    table.addGlobalSecondaryIndex({
      partitionKey: { name: 'Type', type: AttributeType.STRING },
      sortKey: { name: 'IndexSortOrder', type: AttributeType.NUMBER },
      indexName: 'TypeIndexOrder',
    });
    return table;
  }

  private makeDiscordSecret(): ISecret {
    const clientIdParam = new CfnParameter(this, 'DiscordClientId', {
      type: "String",
      noEcho: true,
    });
    const clientSecretParam = new CfnParameter(this, 'DiscordClientSecret', {
      type: "String",
      noEcho: true,
    });
    return new Secret(this, 'DiscordSecret', {
      secretObjectValue: {
        clientId: SecretValue.cfnParameter(clientIdParam),
        clientSecret: SecretValue.cfnParameter(clientSecretParam),
      },
    });
  }

  private makeJwtSecret(): ISecret {
    const jwtPublicParam = new CfnParameter(this, 'JwtPublicKey', {
      type: "String",
      noEcho: true,
    });
    const jwtPrivateParam = new CfnParameter(this, 'JwtPrivateKey', {
      type: "String",
      noEcho: true,
    });
    return new Secret(this, 'JwtSecret', {
      secretObjectValue: {
        publicKey: SecretValue.cfnParameter(jwtPublicParam),
        privateKey: SecretValue.cfnParameter(jwtPrivateParam),
      },
    });
  }

  private makeBackendFunction(dataTable: ITable, domainName: string): IFunction {
    const discordSecret = this.makeDiscordSecret();
    const jwtSecret = this.makeJwtSecret();

    const apiLambda = new DockerImageFunction(this, 'BackendFunction', {
      code: DockerImageCode.fromImageAsset('./../backend/', {
        cmd: ["yellows.api_handler.lambda_handler"],
      }),
      timeout: Duration.minutes(1),
      logRetention: RetentionDays.FIVE_YEARS,
      environment: {
        POWERTOOLS_SERVICE_NAME: 'Yellows-Web',
        DISCORD_OAUTH2_SECRET_ARN: discordSecret.secretArn,
        JWT_SECRET_ARN: jwtSecret.secretArn,
        DDB_TABLE_NAME: dataTable.tableName,
        DOMAIN_NAME: domainName,
      },
      tracing: Tracing.ACTIVE,
    });
    dataTable.grantReadWriteData(apiLambda);
    discordSecret.grantRead(apiLambda);
    jwtSecret.grantRead(apiLambda);

    return apiLambda;
  }

  private makeApiGateway(backendFunction: IFunction): RestApi {
    const accessLogGroup = new LogGroup(this, 'AccessLogGroup', {
      logGroupName: 'Yellows/ApiGateway/access.log',
      retention: RetentionDays.ONE_YEAR,
    });
    return new LambdaRestApi(this, 'ApiGateway', {
      handler: backendFunction,
      deployOptions: {
        accessLogDestination: new LogGroupLogDestination(accessLogGroup),
        accessLogFormat: AccessLogFormat.jsonWithStandardFields(),
        loggingLevel: MethodLoggingLevel.INFO,
        tracingEnabled: true,
      },
    });
  }

  private makeStaticContent(): IBucket {
    const staticBucket = new Bucket(this, 'StaticBucket', {
      encryption: BucketEncryption.S3_MANAGED,
      lifecycleRules: [
        { abortIncompleteMultipartUploadAfter: Duration.days(7) },
        { noncurrentVersionExpiration: Duration.days(7) },
      ],
      blockPublicAccess: {
        blockPublicAcls: true,
        blockPublicPolicy: true,
        ignorePublicAcls: true,
        restrictPublicBuckets: true,
      },
      versioned: true,
    });

    new BucketDeployment(this, 'DeployStatic', {
      sources: [Source.asset('../static/')],
      destinationBucket: staticBucket,
    });

    return staticBucket;
  }

  private makeCloudfrontDistribution(staticBucket: IBucket, apiGw: LambdaRestApi, certificate: ICertificate, domainNames: string[]): IDistribution {
    const cloudfrontOriginAccessIdentity = new OriginAccessIdentity(this, 'CloudfrontOriginAccessIdentity', {
    });
    staticBucket.grantRead(cloudfrontOriginAccessIdentity);

    const apiGatewayOriginRequestPolicy = new OriginRequestPolicy(this, 'CloudfrontApiGwOriginRequestPolicy', {
      headerBehavior: OriginRequestHeaderBehavior.allowList(
        'X-Niax-AHHHHH',
      ),
      cookieBehavior: OriginRequestCookieBehavior.all(),
      queryStringBehavior: OriginRequestQueryStringBehavior.all(),
      originRequestPolicyName: 'ApiGatewayRequestPolicy',
    });

    const defaultBehavior = {
      viewerProtocolPolicy: ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
    };
    const apiGwOrigin = new RestApiOrigin(apiGw);
    const bucketOrigin = new S3Origin(staticBucket, {
      originAccessIdentity: cloudfrontOriginAccessIdentity,
    });
    const cloudfrontDistro = new Distribution(this, "CloudfrontDistro", {
      defaultBehavior: {
        ...defaultBehavior,
        origin: bucketOrigin,
      },
      defaultRootObject: "index.html",
      priceClass: PriceClass.PRICE_CLASS_100,
      minimumProtocolVersion: SecurityPolicyProtocol.TLS_V1_2_2021,
      certificate: certificate,
      domainNames: domainNames,
    });
    cloudfrontDistro.addBehavior('api/*' , apiGwOrigin, {
      ...defaultBehavior,
      originRequestPolicy: apiGatewayOriginRequestPolicy,
      cachePolicy: CachePolicy.CACHING_DISABLED,
      allowedMethods: AllowedMethods.ALLOW_ALL,
      compress: false,
    });

    return cloudfrontDistro;
  }

  private makeDnsRecords(cloudfrontDistro: IDistribution, domainName: string) {
    const zone = HostedZone.fromHostedZoneAttributes(this, 'ParentZone', {
      zoneName: 'niax.uk',
      hostedZoneId: 'Z07942971CJQC1YHKD690'
    });

    new ARecord(this, 'CloudfrontAliasA', {
      zone: zone,
      recordName: domainName,
      target: RecordTarget.fromAlias(new CloudFrontTarget(cloudfrontDistro)),
    });
    new AaaaRecord(this, 'CloudfrontAliasAAAA', {
      zone: zone,
      recordName: domainName,
      target: RecordTarget.fromAlias(new CloudFrontTarget(cloudfrontDistro)),
    });
  }
}
