# backup-to-cloud

<img src="https://github.com/theautomation/kubernetes-gitops/blob/main/assets/img/k8s.png?raw=true" alt="K8s" style="height: 30px; width:30px;"/>
Application running in Kubernetes.

This script is using gnupg to encrypt and sign data.

## Create GPG key

```
gpg --full-generate-key
```

## Export public GPG key

```
gpg --armor --export gpg@theautomation.nl > backup-to-cloud_publickey.asc
```

## Decrypt

```
gpg --decrypt -o <filename>.tar.gz <filename>tar.gz.gpg
```
