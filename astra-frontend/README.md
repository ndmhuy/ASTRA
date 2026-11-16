# React + TypeScript + Vite

This template provides a minimal setup to get React working in Vite with HMR and some Oxlint rules.

Currently, two official plugins are available:

- [@vitejs/plugin-react](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react) uses [Oxc](https://oxc.rs)
- [@vitejs/plugin-react-swc](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react-swc) uses [SWC](https://swc.rs/)

## React Compiler

The React Compiler is not enabled on this template because of its impact on dev & build performances. To add it, see [this documentation](https://react.dev/learn/react-compiler/installation).

## Expanding the Oxlint configuration

If you are developing a production application, we recommend enabling type-aware lint rules by installing `oxlint-tsgolint` and editing `.oxlintrc.json`:

```json
{
  "$schema": "./node_modules/oxlint/configuration_schema.json",
  "plugins": ["react", "typescript", "oxc"],
  "options": {
    "typeAware": true
  },
  "rules": {
    "react/rules-of-hooks": "error",
    "react/only-export-components": ["warn", { "allowConstantExport": true }]
  }
}
```

See the [Oxlint rules documentation](https://oxc.rs/docs/guide/usage/linter/rules) for the full list of rules and categories.

# Running UI + Agent locally

From `astra-frontend`, run `npm run dev`, then open the Local URL printed by Vite.
This command starts the offline Agent on `127.0.0.1:8010`, waits for its health check,
and starts the UI. Keep the terminal running. Ctrl+C stops the processes started by it.
If 5173 is already occupied, Vite prints another port; use that URL.

`npm run dev:ui` starts only Vite and requires an independently running Agent.
`npm run preview` previews static assets; it does not start the Agent or provide its proxy.

If the Agent connection fails, use **Thử lại kết nối**. The existing message/request ID
is preserved; completed UI actions are not repeated when retrying their receipt.
Session and retry data live in memory and disappear on browser reload or Agent restart.

Checks: `npm test`, `npm run build`, `npm run lint`, `npm run test:browser`.
Browser tests require installed Google Chrome and launch an isolated headless profile.
