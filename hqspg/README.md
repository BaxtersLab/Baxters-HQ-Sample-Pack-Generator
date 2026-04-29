# HQSPG — Baxter's HQ Sample Pack Generator (scaffold)

This package contains the Phase 1 scaffolding for HQSPG. It provides:

- `hqspg.cli` — a lightweight CLI entrypoint (placeholder)
- `config/hqspg_default.yaml` — example default configuration

Run the CLI (after installing dependencies) with:

```powershell
python -m hqspg.cli --config config/hqspg_default.yaml
```

Next steps: implement pipeline stages (`loader`, `separator`, `repair`, `extractor`).
