# Setup Kubernetes Cluster on Raspbery Pi
___

# (Master and Node)
___
## Update Firmware

```bash
sudo apt update && sudo apt full-upgrade -y
sudo rpi-eeprom-update -a
```

```bash
sudo reboot
```

If you want to override how much cooling is done on the Pi
```bash
echo 2 | sudo tee /sys/class/thermal/cooling_device0/cur_state
```

# Kubernetes Prerequisites
___
## Update and Install Packages
```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y apt-transport-https ca-certificates curl net-tools gnupg
sudo apt-get update
```

## Enable IPv4 packet forwarding

### sysctl params required by setup, params persist across reboots
```bash
cat <<EOF | sudo tee /etc/sysctl.d/k8s.conf
net.ipv4.ip_forward = 1
EOF
```

### Apply sysctl params without reboot
```bash
sudo sysctl --system
```

## Install runc
```bash
curl -LO https://github.com/opencontainers/runc/releases/download/v1.3.0/runc.arm64
chmod +x runc.arm64
sudo mv runc.arm64 /usr/local/sbin/runc
runc --version
```

## Install CNI
```bash
curl -LO https://github.com/containernetworking/plugins/releases/download/v1.7.1/cni-plugins-linux-arm-v1.7.1.tgz
sudo mkdir -p /opt/cni/bin
sudo tar -C /opt/cni/bin -xzf cni-plugins-linux-arm-v1.7.1.tgz
ls /opt/cni/bin
rm cni-plugins-linux-arm-v1.7.1.tgz
```

## Install containerd
```bash
curl -LO https://github.com/containerd/containerd/releases/download/v2.1.0/containerd-2.1.0-linux-arm64.tar.gz
tar -xvzf containerd-2.1.0-linux-arm64.tar.gz
sudo mv bin/* /usr/local/bin/
containerd --version
rm containerd-2.1.0-linux-arm64.tar.gz
rm -rf bin
```

## Install containerd Service (systemd file)
```bash
sudo curl -o /etc/systemd/system/containerd.service https://raw.githubusercontent.com/containerd/containerd/main/containerd.service
systemctl daemon-reload
systemctl enable --now containerd
sudo systemctl enable containerd
sudo systemctl restart containerd
```

### Install Firewall
```bash
sudo apt update
sudo apt install ufw -y
```

### Firewall (Master ONLY)
```bash
sudo ufw allow 22/tcp
sudo ufw allow 8443/tcp
sudo ufw allow 80/tcp
sudo ufw allow 6443/tcp       # Kubernetes API server
sudo ufw allow 2379:2380/tcp  # etcd server client API
sudo ufw allow 10250/tcp      # Kubelet API
sudo ufw allow 10259/tcp      # kube-scheduler
sudo ufw allow 10257/tcp      # kube-controller-manager
sudo ufw allow 5000/tcp       # Docker Registry
sudo ufw allow 30001/tcp      # Docker Registry External
sudo ufw allow 179/tcp
sudo ufw allow 4789/udp
sudo ufw allow 2379:2380/tcp
```

### Firewall (Node ONLY)
```bash
sudo ufw allow 22/tcp
sudo ufw allow 10250/tcp        # Kubelet API
sudo ufw allow 10256/tcp        # kube-proxy
sudo ufw allow 30000:32767/tcp  # NodePort Services
sudo ufw allow 179/tcp
sudo ufw allow 4789/udp
sudo ufw allow 2379:2380/tcp
```

```bash
sudo ufw enable
```

## Disable Swap
```bash
sudo nano /etc/fstab
```

## Install kubectl
```bash
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/arm64/kubectl"
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/arm64/kubectl.sha256"
echo "$(cat kubectl.sha256)  kubectl" | sha256sum --check
```
## kubectl
```bash
sudo install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl
rm kubectl
rm kubectl.sha256
```

```bash
kubectl version --client
kubectl version --client --output=yaml 
```

```bash
sudo mkdir -p -m 755 /etc/apt/keyrings
curl -fsSL https://pkgs.k8s.io/core:/stable:/v1.32/deb/Release.key | sudo gpg --dearmor -o /etc/apt/keyrings/kubernetes-apt-keyring.gpg
sudo chmod 644 /etc/apt/keyrings/kubernetes-apt-keyring.gpg 
```
This overwrites any existing configuration in /etc/apt/sources.list.d/kubernetes.list
```bash
echo 'deb [signed-by=/etc/apt/keyrings/kubernetes-apt-keyring.gpg] https://pkgs.k8s.io/core:/stable:/v1.32/deb/ /' | sudo tee /etc/apt/sources.list.d/kubernetes.list
sudo chmod 644 /etc/apt/sources.list.d/kubernetes.list   
```
helps tools such as command-not-found to work correctly

```bash
sudo apt-get update
sudo apt-get install -y kubelet kubeadm kubectl
```

# Install K8s Kubernetes
```bash
curl -fsSL https://pkgs.k8s.io/core:/stable:/v1.32/deb/Release.key | sudo gpg --dearmor -o /etc/apt/keyrings/kubernetes-apt-keyring.gpg
```
```bash
echo 'deb [signed-by=/etc/apt/keyrings/kubernetes-apt-keyring.gpg] https://pkgs.k8s.io/core:/stable:/v1.32/deb/ /' | sudo tee /etc/apt/sources.list.d/kubernetes.list
```
```bash
sudo systemctl enable --now kubelet
```

```bash
sudo reboot
```

```bash
sudo kubeadm config images pull
```

## Initializing your control-plane (Master Only) - Please update your IP address here
```bash
sudo kubeadm init \
  --control-plane-endpoint=10.0.0.95:6443 \
  --cri-socket=unix:///var/run/containerd/containerd.sock
```
 (Master Only)
```bash
sudo chown $USER:$USER /etc/kubernetes/admin.conf
```
 (Master Only)
```bash
mkdir -p $HOME/.kube
sudo cp -i /etc/kubernetes/admin.conf $HOME/.kube/config
sudo chown $(id -u):$(id -g) $HOME/.kube/config
export KUBECONFIG=/etc/kubernetes/admin.conf
```
 (Master Only)
```bash
kubectl get nodes
kubectl cluster-info
```

## Install Calico
```bash
kubectl create -f https://raw.githubusercontent.com/projectcalico/calico/v3.29.1/manifests/tigera-operator.yaml
kubectl taint nodes --all node-role.kubernetes.io/control-plane
```

```bash
kubectl apply -f https://docs.projectcalico.org/manifests/calico.yaml
```

# End of Node (Master Only)
___

### Check all Pods
```bash
watch kubectl get pods --all-namespaces
```
wait for all to be running

### Get Detailed Pod Information
```bash
kubectl describe pod <pod-name> -n <namespace>
kubectl describe pod kube-apiserver-k8smaster -n kube-system
kubectl get nodes -o wide
```

## Install Helm
```bash
curl -fsSL -o get_helm.sh https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3
chmod 700 get_helm.sh
./get_helm.sh
helm version
```

## Install Ingress
___
```bash
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/controller-v1.12.0/deploy/static/provider/cloud/deploy.yaml
```
