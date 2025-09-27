import boto3
import botocore.auth
import botocore.awsrequest
from kubernetes import client
from kubernetes.client.rest import ApiException
from datetime import datetime
import base64
import tempfile

def assume_role(role_arn, session_name="LambdaEKSAccessSession", region="ap-northeast-1"):
    sts_client = boto3.client("sts", region_name=region)
    response = sts_client.assume_role(
        RoleArn=role_arn,
        RoleSessionName=session_name
    )
    creds = response["Credentials"]
    return {
        "aws_access_key_id": creds["AccessKeyId"],
        "aws_secret_access_key": creds["SecretAccessKey"],
        "aws_session_token": creds["SessionToken"]
    }

def get_eks_token(cluster_name, region, creds):
    session = boto3.Session(
        aws_access_key_id=creds["aws_access_key_id"],
        aws_secret_access_key=creds["aws_secret_access_key"],
        aws_session_token=creds["aws_session_token"],
        region_name=region
    )
    credentials = session.get_credentials().get_frozen_credentials()
    service = 'sts'
    url = f"https://sts.{region}.amazonaws.com/?Action=GetCallerIdentity&Version=2011-06-15"
    request = botocore.awsrequest.AWSRequest(method='GET', url=url)
    request.headers["x-k8s-aws-id"] = cluster_name
    signer = botocore.auth.SigV4QueryAuth(credentials, service, region, expires=300)
    signer.add_auth(request)
    token = "k8s-aws-v1." + base64.urlsafe_b64encode(request.url.encode("utf-8")).decode("utf-8").rstrip("=")
    return token

def lambda_handler(event, context):
    cluster_name = 'test-base'
    region = 'ap-northeast-1'
    namespace = 'default'
    deployment_name = 'nginx'

    # 引き受けるEKS操作用のロールARN
    eks_operation_role_arn = "arn:aws:iam::335816118727:role/eks-operation-role"

    # sts:AssumeRole で一時的クレデンシャルを取得
    creds = assume_role(eks_operation_role_arn, region=region)

    # 一時クレデンシャルで boto3 EKS クライアント作成
    eks = boto3.client('eks',
                       region_name=region,
                       aws_access_key_id=creds["aws_access_key_id"],
                       aws_secret_access_key=creds["aws_secret_access_key"],
                       aws_session_token=creds["aws_session_token"])
    print(creds["aws_access_key_id"])
    print(creds["aws_secret_access_key"])
    print(creds["aws_session_token"])
    cluster_info = eks.describe_cluster(name=cluster_name)['cluster']
    endpoint = cluster_info['endpoint']
    ca_data = base64.b64decode(cluster_info['certificateAuthority']['data'])
    token = get_eks_token(cluster_name, region, creds)
    print(token)
    print(ca_data.decode('utf-8'))
    print(endpoint)
    with tempfile.NamedTemporaryFile(delete=False) as cert_file:
        cert_file.write(ca_data)
        cert_path = cert_file.name
    print(cert_path)
    configuration = client.Configuration()
    configuration.host = endpoint
    configuration.verify_ssl = True
    configuration.ssl_ca_cert = cert_path
    configuration.api_key = {"authorization": "Bearer " + token}
    client.Configuration.set_default(configuration)

    api = client.AppsV1Api()
    deployments = api.list_namespaced_deployment(namespace=namespace)
    print(deployments)
    try:
        patch_body = {
            "spec": {
                "template": {
                    "metadata": {
                        "annotations": {
                            "kubectl.kubernetes.io/restartedAt": datetime.utcnow().isoformat() + "Z"
                        }
                    }
                }
            }
        }

        api.patch_namespaced_deployment(
            name=deployment_name,
            namespace=namespace,
            body=patch_body
        )
        return {"statusCode": 200, "body": "Deployment restarted annotation patched."}

    except ApiException as e:
        return {"statusCode": e.status, "body": f"Exception when patching deployment: {e}"}
