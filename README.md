# Luminary Cloud Python SDK

Welcome to the official Python SDK for [Luminary Cloud](https://luminarycloud.com) – is a massively scalable simulation platform - the fastest and easiest way to generate vast amounts of simulation data for physics AI, Design Exploration, and Optimization.


This SDK lets you **programmatically orchestrate simulations** on Luminary, integrating directly into your workflows. Whether you're running a single job or sweeping across thousands of designs, this SDK gives you full control to automate and analyze simulations using Python.

Want to get started immediately? Follow our Getting Started tutorial [here](https://app.luminarycloud.com/docs/api/getting-started/first-simulation.html).


---

## Features

- Authenticate securely via API Key or OAuth
- Create and manage simulation projects
- Upload geometry or mesh files
- Generate meshes from CAD automatically
- Configure simulation settings
- Launch and monitor simulation jobs
- Download results (residuals, forces, field data)
- Download images
- Integrate with CAD tools, Blender, or Python-based analysis pipelines

---

## Installation

```bash
pip install luminarycloud
```

Requires Python 3.8 or higher.

---

## Authentication

### Method 1: API Key (recommended for automation)

1. Log in to [Luminary Cloud](https://app.luminarycloud.com)
2. Navigate to **My Account → Profile → API Keys**
3. Create a key and **copy it securely**

Then initialize the SDK:

```python
import luminarycloud as lc

client = lc.Client(api_key="your-api-key")
lc.set_default_client(client)
```

Alternatively, set the environment variable:

```bash
export LC_API_KEY=your-api-key
```

### Method 2: OAuth Login (interactive use)

If no API key is provided, the SDK will open a browser for login and use your session.

---

## Integration Ideas

- Blender or CAD: Automate simulation runs on geometry export
- ML: Train physics AI surrogate models from simulation outputs
- Batch studies: Sweep across parameters or design variations
- Dashboards: Visualize convergence or performance metrics

---

## Tips

- Simulations are **deduplicated** — use unique inputs or names to rerun
- Use `.wait()` on mesh and simulation objects so the script will wait until the process completes to proceed
- Never hardcode API keys in shared code – use environment variables

---

## Documentation

- Full API Reference: [https://app.luminarycloud.com/docs/api/](https://app.luminarycloud.com/docs/api/)
- Tutorials: [https://docs.luminarycloud.com/en/collections/9479898-tutorials](https://docs.luminarycloud.com/en/collections/9479898-tutorials)
- Simulation case studies & examples: Available in your Luminary UI
- AI Assistance: you can ask our AI Assistant to generate code directly in your Luminary UI!

---

## 🛠️ Support

Need help? Contact support via our chat interface at [Luminary Cloud](https://luminarycloud.com).

---

> **Luminary Cloud** is a massively scalable simulation platform - the fastest and easiest way to generate vast amounts of simulation data for physics AI.
```

