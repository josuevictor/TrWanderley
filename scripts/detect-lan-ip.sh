#!/usr/bin/env bash
# IP IPv4 do PC na rede que o telemóvel deve usar (evita Docker 172.x e outras interfaces).
# Uso: source ou LAN_IP=$(./scripts/detect-lan-ip.sh)

set -euo pipefail

if [[ -n "${LAN_IP:-}" ]]; then
  echo "$LAN_IP"
  exit 0
fi

# Melhor: IP local na rota predefínida (campo `src` — não confundir com `via` = gateway)
if command -v ip >/dev/null 2>&1; then
  ip_out="$(ip -4 route get 1.1.1.1 2>/dev/null || true)"
  if [[ -n "$ip_out" ]]; then
    src="$(echo "$ip_out" | sed -n 's/.* src \([0-9][0-9.]*\).*/\1/p' | head -1)"
    if [[ "$src" =~ ^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$ && "$src" != "127.0.0.1" ]]; then
      echo "$src"
      exit 0
    fi
  fi
fi

# Fallback: primeiro candidato de hostname -I que não seja loopback nem típico Docker
if read -r -a ips <<< "$(hostname -I 2>/dev/null)"; then
  for cand in "${ips[@]}"; do
    if [[ "$cand" =~ ^127\. ]]; then continue; fi
    if [[ "$cand" =~ ^169\.254\. ]]; then continue; fi
    if [[ "$cand" =~ ^172\.(1[6-9]|2[0-9]|3[0-1])\. ]]; then continue; fi
    echo "$cand"
    exit 0
  done
fi

echo "" >&2
exit 1
