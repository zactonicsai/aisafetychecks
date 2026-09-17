Packer on macOS: build images from a Mac
Packer is HashiCorp’s tool for turning a template (HCL) into a machine image: Docker image, AWS AMI, Azure image, VMware/Parallels/Tart VM, and more. You describe the image once; Packer launches a source, runs provisioners, then packages the result.
On a Mac this is especially useful because:
	•	You can build Docker images locally with Docker Desktop (no cloud bill).
	•	You can build cloud images (AMIs, etc.) from your laptop using cloud APIs.
	•	You can build macOS VMs with Tart or Parallels on Apple Silicon.
Official current release at the time of writing: Packer 1.16.0.

1. What you need on the Mac
Goal
Extra software
Docker images
Docker Desktop (running)
AWS AMIs
AWS credentials (aws configure or env vars)
macOS VMs (Apple Silicon)
Tart and/or Parallels Desktop
VMware guests (Intel mostly)
VMware Fusion
This tutorial uses Docker first (official HashiCorp getting-started path). Then AWS and macOS VMs.

2. Install Packer on macOS
Homebrew is the supported path. Use HashiCorp’s tap so you get the signed official binary, not a third-party formula.
# If Homebrew is not installed (Apple Silicon):
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

brew tap hashicorp/tap
brew install hashicorp/tap/packer
Verify:
packer version
which packer
Upgrade later:
brew upgrade hashicorp/tap/packer
Binary install (if you skip Homebrew): download darwin_arm64 or darwin_amd64 from developer.hashicorp.com/packer/install, unzip, put packer on your PATH.
Confirm Docker is usable:
docker info
docker pull ubuntu:jammy

3. How a Packer template is structured (HCL2)
Modern Packer templates use HCL2 (.pkr.hcl), same family of language as Terraform. Three root ideas:
	1	packer {} — Packer settings and required plugins.
	2	source "TYPE" "NAME" {} — how to start the machine (the builder).
	3	build {} — what to do after it starts: provisioners + post-processors.
Plugins are not all bundled anymore. You declare them, then packer init downloads them.

4. First image: Ubuntu Docker image on your Mac
This is the official HashiCorp starter. It works fully offline-from-cloud on a Mac with Docker Desktop.
mkdir -p ~/packer_tutorial && cd ~/packer_tutorial
Create docker-ubuntu.pkr.hcl:
packer {
  required_plugins {
    docker = {
      version = ">= 1.0.8"
      source  = "github.com/hashicorp/docker"
    }
  }
}

source "docker" "ubuntu" {
  image  = "ubuntu:jammy"
  commit = true
}

build {
  name = "learn-packer"
  sources = [
    "source.docker.ubuntu"
  ]
}
What each piece does
packer.required_plugins.docker Tells Packer to fetch the Docker builder plugin from github.com/hashicorp/docker, version ≥ 1.0.8.
source "docker" "ubuntu"
	•	Builder type: docker
	•	Local name: ubuntu
	•	image — base image Packer runs (ubuntu:jammy)
	•	commit = true — after provisioners, run docker commit so you get a new image instead of only a .tar export
build Points at that source. Empty of provisioners for now, so the “custom” image is just a committed copy of Ubuntu Jammy.
Commands you always run
# Download plugins declared in the template
packer init .

# Canonical formatting (like terraform fmt)
packer fmt .

# Syntax + config check (no output = valid)
packer validate .

# Build
packer build .
# or: packer build docker-ubuntu.pkr.hcl
packer init . is idempotent: it only downloads what is missing.
Expected flow during packer build:
	1	Pull ubuntu:jammy if needed
	2	docker run a container with Packer’s file-share mount
	3	Connect with the Docker communicator (not SSH)
	4	Commit → print image SHA
	5	Kill the temp container
Then:
docker images
You will see an untagged image whose ID matches Packer’s “Imported Docker image” line. Packer builds images; it does not tag or delete them unless you add post-processors.

5. Provision the image (install software, write files)
Add provisioners inside the build block. They run in order.
packer {
  required_plugins {
    docker = {
      version = ">= 1.0.8"
      source  = "github.com/hashicorp/docker"
    }
  }
}

source "docker" "ubuntu" {
  image  = "ubuntu:jammy"
  commit = true
}

build {
  name = "learn-packer"
  sources = ["source.docker.ubuntu"]

  provisioner "shell" {
    environment_vars = [
      "FOO=hello world",
    ]
    inline = [
      "echo Adding file to Docker container",
      "echo \"FOO is $FOO\" > /example.txt",
      "apt-get update",
      "DEBIAN_FRONTEND=noninteractive apt-get install -y nginx curl",
    ]
  }

  provisioner "shell" {
    inline = [
      "nginx -v",
      "cat /example.txt",
    ]
  }
}
Rebuild:
packer fmt .
packer validate .
packer build .
shell provisioner runs commands inside the guest/container. Use either inline or script / scripts (not both as the only source). environment_vars are injected for that provisioner only.
Upload files from the Mac
provisioner "file" {
  source      = "files/index.html"
  destination = "/tmp/index.html"
}

provisioner "shell" {
  inline = [
    "mv /tmp/index.html /var/www/html/index.html",
  ]
}
The file provisioner can only write where the communicator user can write. Common pattern: drop in /tmp, then mv with sudo (or, in Docker as root, just mv).

6. Variables (don’t hard-code the base image)
variable "docker_image" {
  type        = string
  default     = "ubuntu:jammy"
  description = "Base Docker image"
}

source "docker" "ubuntu" {
  image  = var.docker_image
  commit = true
}

build {
  name    = "learn-packer"
  sources = ["source.docker.ubuntu"]

  provisioner "shell" {
    inline = [
      "echo Building from ${var.docker_image}",
    ]
  }
}
Override at build time:
packer build -var 'docker_image=ubuntu:noble' .
Or a vars file ubuntu.pkrvars.hcl:
docker_image = "ubuntu:noble"
packer build -var-file=ubuntu.pkrvars.hcl .
Sensitive values: variable "token" { type = string; sensitive = true } so they are redacted in logs.

7. Tag the image (post-processor)
A committed Docker image from Packer is untagged. Add a post-processor:
build {
  name    = "learn-packer"
  sources = ["source.docker.ubuntu"]

  provisioner "shell" {
    inline = ["echo ok > /ok.txt"]
  }

  post-processor "docker-tag" {
    repository = "local/ubuntu-nginx"
    tags       = ["jammy", "latest"]
  }
}
After build:
docker images local/ubuntu-nginx
docker run --rm local/ubuntu-nginx:jammy cat /ok.txt
To push: chain docker-tag then docker-push (and log in to the registry first).
You can also set image metadata at commit time with changes on the source (Dockerfile-like instructions):
source "docker" "ubuntu" {
  image  = "ubuntu:jammy"
  commit = true
  changes = [
    "EXPOSE 80",
    "CMD [\"nginx\", \"-g\", \"daemon off;\"]",
    "LABEL built-by=packer",
  ]
}

8. Everyday Packer CLI on macOS
packer version
packer init .                 # install plugins from required_plugins
packer plugins installed      # see what you have
packer fmt .
packer validate .
packer inspect .              # show sources/builds
packer build .
packer build -force .         # overwrite previous artifact if builder supports it
packer build -debug .         # pause between steps; good for SSH troubleshooting
packer build -on-error=ask .  # keep instance / drop to debug on failure
packer build -only='*.docker.ubuntu' .
Debug mode is the most useful flag when a cloud or VM build hangs on SSH.
Plugin cache lives under ~/.packer.d/ (or PACKER_PLUGIN_PATH / PACKER_CONFIG_DIR if you set them). On Mac, if Docker file mounts fail, check Docker Desktop → Settings → Resources → File sharing, and that ~/.packer.d is accessible.

9. Build an AWS AMI from your Mac
Same laptop, different builder. Packer talks to the AWS API, launches an EC2 instance in your account, provisions it over SSH (or SSM), snapshots it as an AMI, then terminates the instance.
Prerequisites:
brew install awscli
aws configure   # or use AWS_PROFILE / env vars
IAM needs permission to run EC2, create AMIs, and (if you use it) SSM.
Example ami-ubuntu.pkr.hcl:
packer {
  required_plugins {
    amazon = {
      source  = "github.com/hashicorp/amazon"
      version = "~> 1"
    }
  }
}

variable "region" {
  type    = string
  default = "us-east-1"
}

data "amazon-ami" "ubuntu" {
  filters = {
    name                = "ubuntu/images/hvm-ssd-gp3/ubuntu-jammy-22.04-amd64-server-*"
    root-device-type    = "ebs"
    virtualization-type = "hvm"
  }
  most_recent = true
  owners      = ["099720109477"] # Canonical
  region      = var.region
}

source "amazon-ebs" "ubuntu" {
  region        = var.region
  source_ami    = data.amazon-ami.ubuntu.id
  instance_type = "t3.micro"
  ssh_username  = "ubuntu"
  ami_name      = "learn-packer-ubuntu-${formatdate("YYYYMMDDhhmmss", timestamp())}"

  tags = {
    Name      = "learn-packer-ubuntu"
    BuiltWith = "Packer"
  }
}

build {
  sources = ["source.amazon-ebs.ubuntu"]

  provisioner "shell" {
    inline = [
      "sudo apt-get update",
      "sudo DEBIAN_FRONTEND=noninteractive apt-get install -y nginx",
      "sudo systemctl enable nginx",
    ]
  }
}
packer init .
packer validate .
packer build -var 'region=us-east-1' .
That costs a few minutes of t3.micro plus the AMI storage. Always confirm the instance is terminated after a failed build (-debug / -on-error=ask leave resources on purpose).
EC2 Mac AMIs are a special case: mac1.metal / mac2.metal need a Dedicated Host, long ssh_timeout, often SSM instead of public SSH, and disk-resize steps with diskutil. That is an advanced AWS workflow, not a local Mac VM build.

10. Building macOS VM images on a Mac
“Packer on macOS” and “Packer building macOS” are different.
Tart (Apple Silicon, popular for CI)
Tart + the tart Packer plugin clone a vanilla macOS VM (Cirrus IPSW-based images), provision over SSH, and save a new Tart VM. Community templates (e.g. Cirrus macos-image-templates) install Homebrew, Xcode CLT, runners, etc.
Typical shape:
packer {
  required_plugins {
    tart = {
      version = ">= 1.12.0"
      source  = "github.com/cirruslabs/tart"
    }
  }
}

source "tart-cli" "macos" {
  vm_name      = "sequoia-dev"
  vm_base_name = "ghcr.io/cirruslabs/macos-sequoia-vanilla:latest"
  cpu_count    = 4
  memory_gb    = 8
  disk_size_gb = 50
  ssh_username = "admin"
  ssh_password = "admin"
  ssh_timeout  = "120s"
}

build {
  sources = ["source.tart-cli.macos"]

  provisioner "shell" {
    inline = [
      "/bin/bash -c \"$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\"",
    ]
  }
}
You need Tart installed (brew install cirruslabs/cli/tart) and enough disk for the base VM.
Parallels Desktop
Parallels publishes Packer examples that boot from an IPSW or an existing .macvm and can emit a Vagrant box. Flow is the same: packer init → validate -var-file=... → build.
VMware Fusion
Older Intel-oriented templates use vmware-iso / vmware-vmx and a prepared installer ISO (often via mist). Apple Silicon + Fusion support is more limited; Tart/Parallels are the usual Apple Silicon path.
Licensing note: automating macOS installs is only appropriate on Apple hardware you are licensed to use.

11. One template, multiple images
You can declare several sources and attach them to one build. Packer runs them in parallel by default:
source "docker" "jammy" {
  image  = "ubuntu:jammy"
  commit = true
}

source "docker" "noble" {
  image  = "ubuntu:noble"
  commit = true
}

build {
  sources = [
    "source.docker.jammy",
    "source.docker.noble",
  ]

  provisioner "shell" {
    inline = ["apt-get update"]
  }
}
Restrict:
packer build -only='*.docker.jammy' .
Use only / except on a provisioner if one source should skip a step.

12. macOS-specific gotchas
	1	Docker Desktop must be running. The Docker builder talks to the local engine, not a remote host. On Mac, that engine is a Linux VM. Give it enough CPU/RAM in Docker settings.
	2	Apple Silicon vs amd64 images. ubuntu:jammy on an M-series Mac is arm64 unless you force a platform. For x86 guests in Docker: source "docker" "ubuntu" {
	3	  image = "ubuntu:jammy"
	4	  commit = true
	5	  # plugin versions vary; if you need amd64 explicitly, pull
	6	  # ubuntu:jammy with --platform linux/amd64 first, or set builder options
	7	  # your plugin version documents.
	8	}
	9	 Cloud AMIs are independent of your laptop CPU: an amazon-ebs build of amd64 works from an M-series Mac because the instance runs in AWS.
	10	File sharing / permissions. Packer stages files under ~/.packer.d (or PACKER_TMP_DIR). If the file provisioner fails on Docker Desktop, add that path to file sharing.
	11	Rosetta / Intel Homebrew leftovers. Official Packer bottles exist for both darwin_arm64 and darwin_amd64. Prefer the native arm64 binary on Apple Silicon.
	12	Long macOS VM boots. Raise ssh_timeout (minutes, not seconds) for Tart/Parallels/Fusion and for EC2 Mac.
	13	Cleanup. Docker images and Tart VMs accumulate. docker image prune and tart delete after experiments.

13. Recommended practice
	•	Keep templates in git; one folder per image family (packer init at that root).
	•	Pin plugin versions (version = "~> 1").
	•	Use variables + .pkrvars.hcl (and gitignore secrets).
	•	Run validate in CI before build.
	•	Prefer idempotent provisioners (apt-get, brew, Ansible).
	•	Tag artifacts (AMI name + timestamp, Docker tags, Tart VM names).
	•	For production golden images, look at HCP Packer to track versions and revoke old images.

14. Minimal “do this now” checklist
brew tap hashicorp/tap
brew install hashicorp/tap/packer
# start Docker Desktop

mkdir -p ~/packer_tutorial && cd ~/packer_tutorial
# paste the provisioned docker-ubuntu.pkr.hcl from section 5

packer init .
packer validate .
packer build .
docker images
That is a complete Packer loop on macOS: plugin install → template → provision → committed image.
If you want the next step as a follow-up, the two most useful extensions from here are (1) a tagged Docker image pushed to GHCR/ECR, or (2) a Tart Sequoia/Tahoe VM with Xcode + Homebrew for iOS CI.
I’ll look up how Packer works with Podman on macOS so the tutorial can include a complete, accurate Podman path.# Packer on macOS with Podman
Packer does not ship a first-party podman builder. On a Mac you keep the official Docker plugin and point it at the Podman CLI with docker_path. HashiCorp documents that option and warns that not every Docker flag is equivalent, so some builds can fail.
On macOS, Podman itself is not native: it runs Linux containers inside a Podman machine (a lightweight VM). You must start that machine before packer build.

1. Install and start Podman
CLI only:
brew install podman

podman machine init --cpus=4 --memory=8192 --disk-size=60
podman machine start
podman info
podman run --rm quay.io/podman/hello
Optional GUI:
brew install --cask podman-desktop
Confirm the machine is up:
podman machine list
You want Running. If Packer later says it cannot talk to a container engine, this is the first thing to check.
Give the VM enough disk. Image pulls + Packer’s temp mounts live there.

2. How Packer talks to Podman
The Docker builder shells out to a binary (docker by default). Set:
docker_path = "podman"
Packer then runs podman pull, podman run, podman exec, podman commit, podman kill instead of the Docker equivalents.
That is the supported path. Do not rely only on alias docker=podman inside Packer — aliases are a shell convenience and Packer may not see them. Point docker_path at the real binary:
which podman
# /opt/homebrew/bin/podman   # Apple Silicon Homebrew
docker_path = "/opt/homebrew/bin/podman"
A community packer-plugin-podman exists (a fork of the Docker plugin). Prefer the official plugin + docker_path unless you have a specific reason to use the fork.

3. Full Podman template
Same structure as the Docker tutorial; only the source changes.
podman-ubuntu.pkr.hcl:
packer {
  required_plugins {
    docker = {
      version = ">= 1.0.8"
      source  = "github.com/hashicorp/docker"
    }
  }
}

variable "base_image" {
  type        = string
  default     = "ubuntu:jammy"
  description = "OCI base image (Docker Hub, pulled by Podman)"
}

variable "podman_bin" {
  type        = string
  default     = "podman"
  description = "Path to the Podman CLI"
}

source "docker" "ubuntu" {
  image       = var.base_image
  commit      = true
  docker_path = var.podman_bin

  changes = [
    "LABEL built-by=packer",
    "LABEL runtime=podman",
    "CMD [\"bash\"]",
  ]
}

build {
  name = "learn-packer-podman"
  sources = ["source.docker.ubuntu"]

  provisioner "shell" {
    inline = [
      "echo Provisioning inside a Podman container",
      "apt-get update",
      "DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends curl ca-certificates",
      "curl --version",
      "echo packer-on-podman > /ok.txt",
    ]
  }
}
Commands:
cd ~/packer_tutorial
packer init .
packer fmt .
packer validate .
packer build -var 'podman_bin=/opt/homebrew/bin/podman' podman-ubuntu.pkr.hcl
On Intel Homebrew the binary is usually /usr/local/bin/podman.
Expected flow (same as Docker, different CLI):
	1	podman pull ubuntu:jammy
	2	podman run a throwaway container
	3	Packer communicator talks to that container
	4	podman commit → new image ID
	5	Container is killed
Verify with Podman, not Docker:
podman images
podman run --rm IMAGE_ID cat /ok.txt
# packer-on-podman
Docker Desktop and Podman keep separate image stores. An image Packer committed with Podman will not show up in docker images.

4. One template, Docker or Podman
Switch engines with a variable so you do not maintain two files:
variable "container_cli" {
  type        = string
  default     = "podman"   # or "docker"
  description = "docker or podman binary"
}

source "docker" "ubuntu" {
  image       = "ubuntu:jammy"
  commit      = true
  docker_path = var.container_cli
}
# Podman
packer build -var 'container_cli=podman' .

# Docker Desktop
packer build -var 'container_cli=docker' .
Only one engine needs to be running for that build.

5. Tag and run the result (important Podman detail)
The builder honors docker_path. The docker-tag / docker-push post-processors still invoke the docker binary unless that name exists on PATH.
If Docker Desktop is not installed, create a shim so post-processors work:
mkdir -p ~/bin
ln -sf "$(which podman)" ~/bin/docker
export PATH="$HOME/bin:$PATH"
Or in ~/.zshrc (interactive only — Packer launched from GUI apps will not see this unless you set it in the environment those apps inherit):
export PATH="$HOME/bin:$PATH"
Then you can add:
build {
  sources = ["source.docker.ubuntu"]

  provisioner "shell" {
    inline = ["echo ok > /ok.txt"]
  }

  post-processor "docker-tag" {
    repository = "localhost/ubuntu-packer"
    tags       = ["jammy", "latest"]
  }
}
After the build:
podman images localhost/ubuntu-packer
podman run --rm localhost/ubuntu-packer:jammy cat /ok.txt
Push:
podman login quay.io
podman tag localhost/ubuntu-packer:jammy quay.io/YOUR_USER/ubuntu-packer:jammy
podman push quay.io/YOUR_USER/ubuntu-packer:jammy
You can also use Packer’s docker-push post-processor once docker on PATH is the Podman shim.

6. File provisioner and mounts on macOS
Packer bind-mounts a temp dir (usually under ~/.packer.d) into the container as /packer-files. On a Mac, Podman machine maps /Users into the VM, so paths under your home directory generally work.
provisioner "file" {
  source      = "files/index.html"
  destination = "/tmp/index.html"
}
If the file provisioner fails with a mount error:
# Confirm the machine is running and /Users is visible
podman machine ssh -- ls /Users

# Force Packer temp files into $HOME
export PACKER_TMP_DIR="$HOME/.packer-tmp"
mkdir -p "$PACKER_TMP_DIR"
packer build .
Do not put Packer temp dirs on volumes the machine cannot see (external disks, iCloud-only paths, some network shares).

7. Optional: Docker-compatible socket
Some tools speak the Docker API (DOCKER_HOST) instead of the CLI. Packer’s Docker builder is CLI-first (docker_path), but it is still useful to point the API at Podman for other tools.
podman machine inspect --format '{{.ConnectionInfo.PodmanSocket.Path}}'
Typical macOS socket:
export DOCKER_HOST="unix://$HOME/.local/share/containers/podman/machine/podman.sock"
Exact path varies by Podman version; always take it from podman machine inspect or:
export DOCKER_HOST="unix://$(podman info -f '{{.Host.RemoteSocket.Path}}')"
Podman Desktop can also enable “third-party Docker tool compatibility,” which maps a Docker-like socket. That helps Testcontainers and similar; it is not required for Packer if docker_path is set.

8. What works vs what bites
Works well:
	•	image + commit = true
	•	shell and file provisioners
	•	changes (LABEL, CMD, ENV, EXPOSE)
	•	Pulling public OCI images (ubuntu, alpine, …)
	•	Apple Silicon arm64 images (native)
Often fine, test first:
	•	privileged = true
	•	extra volumes
	•	private registry login / login_username / login_password
	•	docker-tag after you put a docker → podman shim on PATH
Likely to break or is unsupported:
	•	Windows containers (windows_container = true) — Podman on Mac is Linux-only
	•	Some cap_add / runtime / device combinations
	•	Assuming the image appears in Docker Desktop
	•	Relying on /var/run/docker.sock without configuring the Podman socket
Official warning: not all Docker builder options are equivalent under Podman. If a build fails on an obscure docker run flag, simplify the source (drop privileged, custom run_command, extra devices) and retry.

9. Troubleshooting
Symptom
What to do
Cannot connect to Docker daemon / similar
podman machine start; confirm podman info
Packer still calls docker
Set docker_path to the full path of podman
docker-tag not found
Shim ~/bin/docker → podman and put ~/bin on PATH
File provisioner mount error
PACKER_TMP_DIR=$HOME/.packer-tmp; keep files under /Users
Image missing after “success”
Use podman images, not docker images
Slow first build
Normal: Podman machine + first pull of ubuntu:jammy
platform / amd64 image on M-series
podman pull --platform linux/amd64 ubuntu:jammy first, or use an arm64 base
Both Docker Desktop and Podman running
Fine, but they do not share images. Pick one CLI per build
Debug Packer the same way as with Docker:
packer build -debug -on-error=ask -var 'podman_bin=podman' .
-debug pauses between steps so you can podman ps -a and podman exec the build container.

10. Minimal Podman checklist
brew install podman
podman machine init --cpus=4 --memory=8192 --disk-size=60
podman machine start

# packer + hashicorp/docker plugin already installed from the earlier tutorial

packer init .
packer validate .
packer build -var 'podman_bin=podman' podman-ubuntu.pkr.hcl

podman images
That is the full loop: Packer on macOS, official Docker plugin, Podman as the runtime.
AWS AMI and Tart/Parallels macOS VM builds from the previous section are unchanged — they never used Docker or Podman. Only the local container image path switches engines.
