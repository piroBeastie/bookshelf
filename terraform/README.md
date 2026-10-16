# terraform

The AWS infrastructure BookShelf would run on: a VPC with two public subnets, the
IAM roles EKS needs, an EKS cluster and a managed node group.

| file | what is in it |
|---|---|
| `versions.tf` | required Terraform and provider versions, the provider block, default tags |
| `variables.tf` | region, environment, cluster name, CIDRs, instance type, node count |
| `network.tf` | VPC, internet gateway, two public subnets, route table and associations |
| `eks.tf` | IAM roles and policy attachments, the EKS cluster, the managed node group |
| `outputs.tf` | VPC and subnet ids, cluster name and endpoint, the `update-kubeconfig` command |
| `terraform.tfvars.example` | copy to `terraform.tfvars` and edit; the real file is gitignored |

## Running it

```bash
cp terraform.tfvars.example terraform.tfvars

terraform init
terraform fmt -check -recursive
terraform validate
terraform plan -out=tfplan      # 15 resources

terraform apply tfplan          # creates real, billable AWS resources
aws eks update-kubeconfig --region ap-south-1 --name bookshelf-eks
helm upgrade --install bookshelf ../helm/bookshelf -n bookshelf --create-namespace

terraform destroy               # always, when you are finished
```

Credentials never live in this folder. They come from the environment
(`AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY`), from `aws sso login`, or from an
IAM role. `terraform.tfvars`, `.terraform/` and every state file are gitignored.

## Two deliberate choices

**No community modules.** `terraform-aws-modules/vpc` and `.../eks` are shorter,
but they hide the IAM wiring, which is the part worth learning: one role for the
control plane (`AmazonEKSClusterPolicy`) and one for the nodes
(`AmazonEKSWorkerNodePolicy` + `AmazonEKS_CNI_Policy` +
`AmazonEC2ContainerRegistryReadOnly`). Writing them out also means this config
contains **no data sources**, which is what lets `terraform plan` run without
credentials at all.

**Two public subnets, no NAT gateway.** EKS refuses to create a cluster in a
single availability zone, so there are two — `ap-south-1a` and `ap-south-1b`. A
production layout would put the nodes in private subnets behind a NAT gateway;
that NAT gateway is also the most expensive thing in a small VPC, billed hourly
plus data, so it is left out here.

## What was actually run

`init`, `fmt`, `validate` and `plan` — all clean, 15 resources planned.

`apply` and `destroy` were **not** run: there is no AWS account with billing
behind this project, so no VPC or cluster was ever created and there is no AWS
Console screenshot. The plan is genuine; it executes against the real AWS
provider with the credential calls skipped, which only works because of the
no-data-sources choice above. This is also listed under **Known issues and
limitations** in the root README.

## Cost, if you do run it

The EKS control plane bills per hour whether or not anything is deployed on it,
and two `t3.medium` nodes bill on top of that. Nothing here is free tier. Run
`terraform destroy` as soon as you have your screenshots.
