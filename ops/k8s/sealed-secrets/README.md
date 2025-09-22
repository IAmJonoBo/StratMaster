# Sealed Secrets Runbook

This runbook documents how we bootstrap Bitnami Sealed Secrets in StratMaster
clusters and how it interacts with our SOPS+age workflow. Apply it to both dev
and long-lived environments to guarantee deterministic secret provisioning.

## Bootstrap flow

1. **Install the controller.**

   ```bash
   kubectl apply -f https://github.com/bitnami-labs/sealed-secrets/releases/download/v0.26.3/controller.yaml
   ```

   - Pin the version in `helmfile.d` when moving to Helm management.
   - Verify the controller is healthy: `kubectl -n kube-system rollout status deploy sealed-secrets-controller`.

2. **Generate a cluster key.**
   - For ephemeral preview environments rely on the auto-generated key pair.
   - For staging/prod, generate an offline key so you can recover seals if the
     namespace is deleted:
     ```bash
     kubectl -n kube-system create secret generic sealed-secrets-key \
       --from-file=private-key=master.key --from-file=public-key=master.pub \
       --dry-run=client -o yaml | kubectl apply -f -
     ```
3. **Distribute the public cert.**
   - Export via `kubeseal --fetch-cert > ops/k8s/sealed-secrets/certs/<cluster>.pem`.
   - Commit the PEM so CI and developer machines can reseal secrets without
     contacting the cluster.
4. **Gate access with RBAC.**
   - Only allow the platform automation SA to manage the controller secret.
   - Rotate permissions alongside `cluster-admin` grants during environment creation.

## Authoring sealed manifests

- Use SOPS as the canonical authoring tool (`.sops.yaml` maps to secret paths).
- Encrypt raw YAML first, then seal the SOPS output:
  ```bash
  sops ops/k8s/secrets/temporal-admin.yaml   # edit using age recipients
  sops -d ops/k8s/secrets/temporal-admin.yaml \
    | kubeseal --cert ops/k8s/sealed-secrets/certs/staging.pem \
    > ops/k8s/sealed-secrets/temporal-admin.enc.yaml
  ```
- Every sealed secret lives beside the workload chart (`ops/k8s/<component>/secrets`).
  Use annotations so platform automation can pick the right secret during deploy.

## Key management strategy

| Environment | Source of truth                   | Rotation cadence | Storage                            |
| ----------- | --------------------------------- | ---------------- | ---------------------------------- |
| `dev`       | Controller-managed (auto rotate)  | N/A (ephemeral)  | Namespace secret                   |
| `staging`   | Offline age identity (`ops/keys`) | 6 months         | Vault (sealed) + Git (public cert) |
| `prod`      | Offline HSM-backed identity       | 3 months         | Vault (sealed) + secure enclave    |

- Store private keys in Vault using the platform automation namespace (see
  `ops/policies/sealed_secrets.hcl`).
- Mirror keys into the DR region by exporting the sealed secret and applying to
  the standby cluster before failover tests.

## SOPS + age workflow

1. Age keysets live under `ops/keys/age/<cluster>.txt` and are synced to Vault.
2. `.sops.yaml` targets the correct recipients by folder, so editing a secret just
   works with `sops <file>`.
3. After saving, run `make secrets.check` to ensure files decrypt cleanly and that
   the plaintext never leaks into Git.
4. Finally reseal into `ops/k8s/sealed-secrets/*.enc.yaml` using the exported PEM.

### Rotation policy

- Generate a new age identity with `age-keygen` and update `.sops.yaml` recipients.
- Re-encrypt all SOPS files (`scripts/rotate_sops_keys.sh` handles the loop).
- Re-seal each secret using the new PEM from the controller.
- Delete the previous controller secret after verifying the rollout completed:
  ```bash
  kubectl -n kube-system delete secret sealed-secrets-key-old
  ```
- Document the rotation in `ops/change-log.md` including the age fingerprint and
  the sealed-secrets controller version.

## Disaster recovery

- Keep an offline copy of the last rotation key in Vault and as a GPG encrypted
  file in the security team password store.
- To recover, reinstall the controller and reapply the saved secret, then re-run
  `kubeseal --recovery-unseal --controller-namespace kube-system` on affected
  manifests.
- Quarterly drills: restore the staging key into a kind cluster and ensure all
  secrets decrypt correctly.

## Integrations

- Flux/Argo CD pipelines only require the sealed YAML; the controller decrypts at
  runtime.
- GitHub Actions runners use `kubeseal --cert <cluster>.pem` in the release
  workflows so credentials never touch the logs.
- Ensure platform CI enforces the `sealed-secrets.bitnami.com/sealed-secrets-key` label
  before apply to avoid unsealed resources creeping in.
