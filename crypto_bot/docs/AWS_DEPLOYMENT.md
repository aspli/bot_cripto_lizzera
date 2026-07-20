# AWS EC2 Deployment Guide

## 1. Launch EC2 Instance
- Go to AWS Management Console -> EC2 -> Launch Instance.
- Choose **Ubuntu 22.04 LTS**.
- Instance Type: `t2.micro` or `t3.small`.
- Create/Select a Key Pair for SSH access.
- Configure Security Group: Allow inbound SSH (port 22).

## 2. Connect to EC2
```bash
ssh -i /path/to/your-key.pem ubuntu@<your-ec2-ip>
```

## 3. Install Docker and Docker Compose
```bash
sudo apt update
sudo apt install -y docker.io docker-compose
sudo systemctl enable --now docker
sudo usermod -aG docker ubuntu
# Log out and log back in to apply group changes
```

## 4. Clone Repository
```bash
git clone <your-repo-url>
cd crypto_bot
```

## 5. Configure Environment Variables
```bash
cp .env.example .env
nano .env
# Fill in your API keys and configuration
```

## 6. Run the Application
```bash
docker-compose up -d --build
```

## 7. Monitoring
- View logs: `docker-compose logs -f bot`
- Telegram alerts will notify you of any trades or errors.
