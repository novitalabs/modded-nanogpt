#!/usr/bin/env bash
set -euo pipefail

POD="${MODDED_NANOGPT_POD_75:-modded-nanogpt-repro-75}"
NODE="${MODDED_NANOGPT_NODE_75:-host-172-31-13-75}"
IMAGE="${MODDED_NANOGPT_IMAGE:-docker.io/vllm/vllm-openai:v0.22.0}"
HOST_REPO="${MODDED_NANOGPT_HOST_REPO:-/data/develop/modded-nanogpt}"
MOUNT_REPO="${MODDED_NANOGPT_MOUNT_REPO:-/workspace/modded-nanogpt}"

if kubectl get pod "${POD}" >/dev/null 2>&1; then
  phase="$(kubectl get pod "${POD}" -o jsonpath='{.status.phase}')"
  node="$(kubectl get pod "${POD}" -o jsonpath='{.spec.nodeName}')"
  echo "pod=${POD} phase=${phase} node=${node}"
  if [[ "${phase}" != "Running" ]]; then
    kubectl describe pod "${POD}" || true
    exit 2
  fi
else
  tmp="$(mktemp)"
  cat > "${tmp}" <<YAML
apiVersion: v1
kind: Pod
metadata:
  name: ${POD}
  labels:
    run: ${POD}
    arthur-agent: modded-nanogpt
spec:
  restartPolicy: Never
  hostNetwork: true
  hostIPC: true
  nodeName: ${NODE}
  containers:
  - name: ${POD}
    image: ${IMAGE}
    imagePullPolicy: IfNotPresent
    command: ["bash", "-lc", "sleep infinity"]
    workingDir: ${MOUNT_REPO}
    env:
    - name: HF_HOME
      value: ${MOUNT_REPO}/.cache/huggingface
    - name: TORCHINDUCTOR_CACHE_DIR
      value: ${MOUNT_REPO}/.cache/torchinductor
    - name: TRITON_CACHE_DIR
      value: ${MOUNT_REPO}/.cache/triton
    - name: http_proxy
      value: http://127.0.0.1:1083
    - name: https_proxy
      value: http://127.0.0.1:1083
    - name: HTTP_PROXY
      value: http://127.0.0.1:1083
    - name: HTTPS_PROXY
      value: http://127.0.0.1:1083
    - name: NO_PROXY
      value: localhost,127.0.0.1,::1,10.0.0.0/8,172.16.0.0/12,192.168.0.0/16,.cluster.local
    - name: no_proxy
      value: localhost,127.0.0.1,::1,10.0.0.0/8,172.16.0.0/12,192.168.0.0/16,.cluster.local
    resources:
      requests:
        nvidia.com/gpu: "8"
      limits:
        nvidia.com/gpu: "8"
    volumeMounts:
    - name: repo
      mountPath: ${MOUNT_REPO}
    - name: dshm
      mountPath: /dev/shm
  volumes:
  - name: repo
    hostPath:
      path: ${HOST_REPO}
      type: Directory
  - name: dshm
    emptyDir:
      medium: Memory
      sizeLimit: 64Gi
YAML
  kubectl apply -f "${tmp}"
  rm -f "${tmp}"
  kubectl wait --for=condition=Ready "pod/${POD}" --timeout=10m
fi

kubectl exec "${POD}" -- bash -lc "
set -euo pipefail
cd '${MOUNT_REPO}'
test -f train_gpt.py
test -d data/fineweb10B
nvidia-smi --query-gpu=index,name,memory.used,memory.total,utilization.gpu --format=csv,noheader
python - <<'PY'
import torch, triton
print('torch', torch.__version__, 'cuda', torch.version.cuda)
print('triton', triton.__version__)
print('cuda_devices', torch.cuda.device_count())
PY
"
