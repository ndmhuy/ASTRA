# Run ASTRA locally

See the [local quickstart](../../README.md#run-locally). On a fresh checkout, run
`.\start.cmd`, paste your own Claude API key in the masked AI connection dialog,
then save. ASTRA keeps that key in the ignored root `.env` and uses it for both
chat and exam generation.

The former team Worker profile has been removed from the current checkout.
The [Chat runbook](WORKER_RUNBOOK.md) and [MAS runbook](MAS_WORKER_RUNBOOK.md)
remain available for operators using private profiles. Previously tracked Worker
tokens can still exist in history and require separate rotation to revoke them.
