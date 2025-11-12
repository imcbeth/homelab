## Localstack Notes:

Get the application URL by running these commands:

```
export NODE_PORT=$(kubectl get --namespace "localstack" -o jsonpath="{.spec.ports[0].nodePort}" services localstack)
export NODE_IP=$(kubectl get nodes --namespace "localstack" -o jsonpath="{.items[0].status.addresses[0].address}")
echo http://$NODE_IP:$NODE_PORT--kubectl get pods -n localstack
```

`kubectl get svc -n localstack`

## READ THIS : I have configured LB on this so port forwarded in not needed
`kubectl -n localstack port-forward svc/localstack 4566:4566`

## Configuring AWS client (aws command fu)

# with Port FWD
`alias aws="aws --endpoint-url=http://localhost:4566"`

# Using LB
`alias aws="aws --endpoint-url=https://localstack.k8s.n37.ca"`

```
export AWS_ACCESS_KEY_ID=test
export AWS_SECRET_ACCESS_KEY=test
export AWS_DEFAULT_REGION=us-east-1
aws s3api list-buckets
```

```
aws iam create-user --user-name <username>
aws iam attach-user-policy --user-name <username> --policy-arn=arn:aws:iam::aws:policy/AmazonEC2FullAccess
aws iam list-attached-user-policies --user-name <username>
aws iam create-access-key --user-name <username>
```