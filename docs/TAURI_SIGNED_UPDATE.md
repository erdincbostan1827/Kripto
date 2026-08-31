# Tauri signed update contract

The optional desktop client initializes the Tauri v2 updater plugin, but a production update channel is **disabled until an operator supplies a real Tauri signer public key and an HTTPS endpoint**. No private signing key is stored in this repository.

Tauri v2 requires signed updater artifacts; signature verification is not treated as optional. The private key belongs only in the release/signing environment (`TAURI_SIGNING_PRIVATE_KEY` / secret manager), while the public key is embedded into the updater configuration used by the client.

Generate the deployment fragment only with real release material:

```bash
python scripts/configure_tauri_updater.py \
  --public-key "<TAURI_SIGNER_PUBLIC_KEY_CONTENT>" \
  --endpoint "https://releases.example.invalid/{{target}}/{{arch}}/{{current_version}}" \
  --output frontend/src-tauri/tauri.updater.production.json
```

The generator fails closed for placeholders, non-HTTPS endpoints, URL credentials, invalid-certificate opt-outs and invalid-hostname opt-outs. `createUpdaterArtifacts` is enabled only in the generated production fragment. A real desktop build, signing key, signed updater artifact and installation-time signature verification remain external acceptance requirements until executed on a real Rust/Tauri build host.
