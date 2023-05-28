# backup-to-cloud

<img src="https://github.com/theautomation/kubernetes-gitops/blob/main/assets/img/k8s.png?raw=true" alt="K8s" style="height: 30px; width:30px;"/>
Application running in Kubernetes.


This script is using gnupg to encrypt and sign data.

## Create GPG key
```bash
gpg --full-generate-key
```

## Export public GPG key
```bash
gpg --armor --export gpg@theautomation.nl > backup-to-cloud_publickey.asc
```