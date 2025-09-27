create-cluster:
	aws cloudformation deploy --stack-name=eksctl-test-base-cluster --template-file ./eksctl-test-cluster.yaml --capabilities CAPABILITY_NAMED_IAM
create-ng:
	aws cloudformation deploy --stack-name=eksctl-test-base-nodegroup-ng --template-file ./eksctl-test-nodegroup-ng.yaml --capabilities CAPABILITY_NAMED_IAM