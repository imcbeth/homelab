## Homelab

Outline of setup / repo frame work / bits of helpful code for my k8s cluster

## `/apps`

Containerized applications:

* `/DockerFiles` - Containers I have created for my kubernetes cluster (arm64)


## `/manifests`

* `/applications` - contains ArgoCD applications deploying all other manifests
* `/base` - contains kustomizations + charts to deploy the applications

