import { Stack, StackProps } from 'aws-cdk-lib';
import { Certificate, CertificateValidation, ICertificate } from 'aws-cdk-lib/aws-certificatemanager';
import { Construct } from 'constructs';
import { HostedZone } from 'aws-cdk-lib/aws-route53';

export interface CertificateStackProps extends StackProps {
  domainName: string,
}

export class CertificateStack extends Stack {
  public readonly certificate: ICertificate;
  constructor(scope: Construct, id: string, props: CertificateStackProps) {
    super(scope, id, props);

    const zone = HostedZone.fromHostedZoneAttributes(this, 'ParentZone', {
      zoneName: 'niax.uk',
      hostedZoneId: 'Z07942971CJQC1YHKD690'
    });

    this.certificate = new Certificate(this, 'AcmCertificate', {
      domainName: props.domainName,
      validation: CertificateValidation.fromDns(zone),
    });

    this.exportValue(this.certificate.certificateArn);
  }
}
