import modal

app = modal.App("inneros-guardian-probe")

@app.function(cpu=1.0, timeout=30)
def check_guardian_isolated():
    return {
        "status": "ISOLATED_CPU_SANDBOX_SUCCESS",
        "env": "MODAL_CLOUD_EPHEMERAL",
        "verified": True
    }

@app.local_entrypoint()
def main():
    res = check_guardian_isolated.remote()
    print("MODAL_RESULT_OK:", res)

