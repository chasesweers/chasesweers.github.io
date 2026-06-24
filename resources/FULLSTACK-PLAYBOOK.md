# The Modern Full-Stack Web App Playbook

*A practical, tool-by-tool guide to building, testing, and shipping a typed, test-driven web application.*

This document captures an entire real-world workflow — from an empty folder to a tested, CI-validated full-stack
app — and explains **each tool, why it's used, and exactly how to wire it up**. It is written to be **general**:
you can follow it for almost any project. Where it helps to be concrete, it references a reference implementation
(a Next.js app called *NetworkMe2*) inside **"In this repo"** callouts so you can see how a theory maps to practice.

> **How to read this**
> Each major section is self-contained: a short *what & why*, the *exact setup commands*, a *representative code
> snippet*, and (where relevant) an *"In this repo"* note showing one real-world choice. Read top to bottom to
> recreate the whole stack, or jump to the layer you need.

---

## Table of Contents

1. [Philosophy](#1-philosophy)
2. [Tech Stack at a Glance](#2-tech-stack-at-a-glance)
3. [Prerequisites & Environment (Node.js)](#3-prerequisites--environment-nodejs)
4. [Project Scaffolding](#4-project-scaffolding)
5. [Version Control — Git & GitHub](#5-version-control--git--github)
6. [Frontend](#6-frontend)
   - 6.1 [Routing & structure (Next.js App Router)](#61-routing--structure-nextjs-app-router)
   - 6.2 [React fundamentals](#62-react-fundamentals)
   - 6.3 [Styling (Tailwind CSS v4)](#63-styling-tailwind-css-v4)
   - 6.4 [State management (Redux Toolkit)](#64-state-management-redux-toolkit)
   - 6.5 [Forms (React Hook Form + Zod)](#65-forms-react-hook-form--zod)
7. [Backend](#7-backend)
   - 7.1 [API route handlers](#71-api-route-handlers)
   - 7.2 [Database (SQLite via better-sqlite3)](#72-database-sqlite-via-better-sqlite3)
   - 7.3 [Authentication (JWT + bcrypt)](#73-authentication-jwt--bcrypt)
   - 7.4 [Route protection (middleware)](#74-route-protection-middleware)
   - 7.5 [Input validation, rate limiting, email](#75-input-validation-rate-limiting--transactional-email)
   - 7.6 [Security headers](#76-security-headers)
8. [Docker](#8-docker)
9. [Testing — the TDD Workflow](#9-testing--the-tdd-workflow)
   - 9.1 [Unit testing (Vitest)](#91-unit-testing-vitest)
   - 9.2 [Integration testing (Vitest + RTL + MSW)](#92-integration-testing-vitest--react-testing-library--msw)
   - 9.3 [End-to-end testing (Playwright)](#93-end-to-end-testing-playwright)
10. [CI/CD — GitHub Actions](#10-cicd--github-actions)
11. [Architecture Decision Records (ADRs)](#11-architecture-decision-records-adrs)
12. [Recreation Checklist](#12-recreation-checklist)
13. [Appendix — Dependencies & Command Cheat-Sheet](#13-appendix--dependencies--command-cheat-sheet)

---

## 1. Philosophy

Two ideas anchor this entire stack:

1. **Everything is typed, end to end.** TypeScript runs from the database row, through the API, into the Redux
   store, and out to the React component. Runtime validation (Zod) guards the boundaries where untyped data
   enters (HTTP request bodies, form input). The compiler catches the rest.

2. **Tests come first (TDD).** No feature is written before a failing test describes it. The cycle is always
   **Red → Green → Refactor**: write a test that fails, write the minimum code to make it pass, then clean up
   while the test holds you safe. This keeps a fast-moving codebase from rotting.

A useful mental model of the test pyramid used here:

```
        /\        E2E (Playwright)        — few, slow, high-confidence: real browser, real server
       /  \
      /----\      Integration (Vitest+RTL) — many: a component + its store + mocked network
     /      \
    /--------\    Unit (Vitest)            — most: pure functions & state logic, no DOM/network
```

---

## 2. Tech Stack at a Glance

| Layer | Tool | Role |
|------|------|------|
| **Runtime** | Node.js 22 | JavaScript runtime for dev server, build, and tests |
| **Language** | TypeScript 5 | Static typing across the whole codebase |
| **Framework** | Next.js 16 (App Router) | Full-stack React framework: routing, SSR, API routes, bundling |
| **UI library** | React 19 | Component model and rendering |
| **Styling** | Tailwind CSS v4 | Utility-first CSS, dark mode, no separate stylesheet sprawl |
| **Client state** | Redux Toolkit + React-Redux | Predictable global state, memoized selectors |
| **Forms** | React Hook Form + Zod | Performant forms with schema-based validation |
| **Database** | SQLite (`better-sqlite3`) | Embedded, zero-config relational store (swappable for Postgres) |
| **Auth** | `bcryptjs` + `jsonwebtoken` / `jose` | Password hashing + stateless JWT sessions |
| **Email** | Resend | Transactional email (e.g. password-reset links) |
| **Unit/Integration tests** | Vitest + jsdom + React Testing Library | Fast tests for logic and components |
| **Network mocking** | MSW *(or `vi.spyOn(fetch)`)* | Intercept HTTP in tests |
| **E2E tests** | Playwright | Drive a real browser against a running app |
| **Linting** | ESLint 9 (flat config) | Catch errors and enforce conventions |
| **CI** | GitHub Actions | Run tests + build on every push/PR |
| **Containers** | Docker / Docker Compose | Reproducible runtime and local services |

> **In this repo:** exact pinned versions are Next.js `16.2.6`, React `19.2.4`, Redux Toolkit `^2.12`,
> Tailwind `^4`, Vitest `^4.1.8`, Playwright `^1.60`, `better-sqlite3 ^12.10`. See the [Appendix](#13-appendix--dependencies--command-cheat-sheet).

---

## 3. Prerequisites & Environment (Node.js)

**What & why.** Node.js runs everything outside the browser: the dev server, the production build, the test
runner, and (for this stack) the database driver. Pin a single Node version so your machine and CI agree.

**Install & pin.**

```bash
# Install nvm (Node Version Manager), then:
nvm install 22
nvm use 22
node -v        # v22.x.x
```

Pin the version for the whole team by committing an `.nvmrc`:

```bash
echo "22" > .nvmrc      # `nvm use` now auto-selects Node 22 in this folder
```

Use **npm** as the package manager (ships with Node). The lockfile (`package-lock.json`) must be committed — CI
installs from it with `npm ci` for byte-for-byte reproducible installs.

> **In this repo:** CI runs on **Node 22** (`.github/workflows/ci.yml`). There is no `.nvmrc` yet — adding one is
> a recommended improvement so local environments match CI automatically.

---

## 4. Project Scaffolding

**What & why.** `create-next-app` generates a batteries-included Next.js project: TypeScript, the App Router,
ESLint, and a Tailwind option, all pre-wired.

```bash
npx create-next-app@latest my-app --typescript --eslint --app --tailwind --src-dir=false --import-alias "@/*"
cd my-app
npm run dev        # http://localhost:3000
```

**Directory conventions.** A predictable layout keeps a growing app navigable. A good convention:

```
my-app/
├── app/                  # App Router: routes, layouts, pages, and API handlers
│   ├── api/              #   server-side route handlers (the "backend")
│   ├── layout.tsx        #   root layout (wraps every page)
│   ├── page.tsx          #   "/" route
│   └── globals.css       #   global stylesheet (Tailwind entry)
├── components/<domain>/  # React components grouped by feature (auth/, graph/, …)
├── stores/               # Redux slices + store config
├── lib/                  # framework-agnostic helpers (db, auth, utils)
├── tests/                # unit / integration / e2e tests + specs
├── next.config.ts
├── tsconfig.json
└── package.json
```

**TypeScript config.** Two settings matter most: `strict` (turns on all type-safety checks) and a path alias so
imports read `@/lib/db` instead of `../../../lib/db`.

```jsonc
// tsconfig.json (excerpt)
{
  "compilerOptions": {
    "strict": true,
    "moduleResolution": "bundler",
    "jsx": "react-jsx",
    "paths": { "@/*": ["./*"] }   // import { x } from '@/lib/x'
  }
}
```

> **Convention used in this repo:** pages under `app/<route>/page.tsx` are kept as *thin wrappers* — all real
> logic lives in `components/` and `stores/`. This keeps routing trivial and logic testable in isolation.

---

## 5. Version Control — Git & GitHub

**What & why.** Git tracks history; GitHub hosts the remote and runs CI. Initialize early and commit in small,
meaningful steps.

```bash
git init
git add .
git commit -m "Initial commit from Create Next App"

# Create the remote (GitHub CLI) and push
gh repo create my-app --private --source=. --remote=origin --push
# …or manually:
git remote add origin https://github.com/<you>/my-app.git
git branch -M main
git push -u origin main
```

**Commit conventions.** Keep messages short and imperative, one logical change per commit
("Add CI workflow", "Password reset", "Fix flaky tests"). This makes history readable and `git revert` surgical.

**`.gitignore` strategy.** Ignore anything generated, secret, or local-only:

```gitignore
/node_modules          # dependencies (reinstalled from lockfile)
/.next/                # Next.js build output
/coverage              # test coverage reports
/playwright-report     # E2E reports
/test-results
.env*                  # secrets — NEVER commit these
*.pem
.DS_Store
data/                  # local database files
*.tsbuildinfo
next-env.d.ts
```

> **A nuance worth copying:** in this repo, *local working documents* are also gitignored — `*.feature`
> (Gherkin specs), `/docs/adr/` (decision records), and `CLAUDE.md` (assistant instructions). The reasoning:
> they're scaffolding for *how* the work is done, not part of the shipped product. **Tests, by contrast, are
> committed** — they are the executable contract for the code.

**Branching.** For solo work, short-lived feature branches merged into `main` via Pull Request is enough — the
PR is what triggers CI (Section 10). Protect `main` so nothing merges with red tests.

---

## 6. Frontend

### 6.1 Routing & structure (Next.js App Router)

**What & why.** The App Router maps the `app/` filesystem to URLs. No router config — the folder structure *is*
the route table.

| File / folder | Becomes | Purpose |
|---|---|---|
| `app/page.tsx` | `/` | a page |
| `app/about/page.tsx` | `/about` | nested page |
| `app/profile/[id]/page.tsx` | `/profile/:id` | dynamic segment |
| `app/(marketing)/page.tsx` | `/` | **route group** — folder in `()` organizes files without affecting the URL |
| `app/layout.tsx` | — | shared shell wrapping all child pages (nav, providers) |
| `app/api/things/route.ts` | `/api/things` | server endpoint (see [Backend](#7-backend)) |

**Root layout** is where you mount global providers (state, theme) and chrome (nav):

```tsx
// app/layout.tsx
import { StoreProvider } from "@/components/StoreProvider";
import { ThemeProvider } from "@/components/ThemeProvider";
import { Nav } from "@/components/Nav";
import "./globals.css";

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <StoreProvider>
          <ThemeProvider>
            <Nav />
            {children}
          </ThemeProvider>
        </StoreProvider>
      </body>
    </html>
  );
}
```

**Server vs. client components.** App Router components are *server components* by default (they render on the
server and ship no JS). Add the `"use client"` directive at the top of any file that needs browser-only features:
state, effects, event handlers, or access to the Redux store.

```tsx
"use client";
import { useState } from "react";
export function Counter() {
  const [n, setN] = useState(0);
  return <button onClick={() => setN(n + 1)}>{n}</button>;
}
```

> **In this repo:** routes include static pages (`/search`, `/graph`, `/import`), dynamic ones
> (`/profile/[key]`, `/shared/[token]`, `/admin/users/[userId]`), and a route group `(onboarding)` for the
> welcome flow. Interactive views are client components; pages stay thin.

### 6.2 React fundamentals

**What & why.** React renders UI as a function of state. The core hooks you'll use constantly:

| Hook | Use it for |
|---|---|
| `useState` | local component state (form text, toggles, loading flags) |
| `useEffect` | side effects after render (fetch, subscriptions, syncing to storage) |
| `useRef` | a mutable value that survives renders without causing one (DOM nodes, guards) |
| `useCallback` / `useMemo` | stabilize functions/values passed to children or deps |
| `useLayoutEffect` | effects that must run *before* the browser paints (measuring/animating DOM) |

```tsx
"use client";
import { useEffect, useState } from "react";

export function Clock() {
  const [now, setNow] = useState(() => new Date());
  useEffect(() => {
    const id = setInterval(() => setNow(new Date()), 1000);
    return () => clearInterval(id);   // cleanup on unmount
  }, []);                              // [] = run once
  return <time>{now.toLocaleTimeString()}</time>;
}
```

> **In this repo:** a `<StoreProvider>` uses a `useRef` "hydration guard" so persisted state loads from
> `localStorage` exactly once on mount, and a canvas-based graph view uses `useRef` + `useLayoutEffect` to drive
> a physics simulation against the `<canvas>` element.

### 6.3 Styling (Tailwind CSS v4)

**What & why.** Tailwind is utility-first: you compose styles from small classes (`flex`, `p-4`, `text-gray-900`)
directly in JSX, instead of writing and naming CSS. v4 is **CSS-first** — configuration lives in your stylesheet,
not a big JS config file.

**Setup (v4).** Tailwind v4 plugs into PostCSS:

```js
// postcss.config.mjs
const config = { plugins: { "@tailwindcss/postcss": {} } };
export default config;
```

```css
/* app/globals.css — the entire Tailwind setup */
@import "tailwindcss";

/* enable class-based dark mode: `dark:` variants apply under a .dark ancestor */
@variant dark (&:is(.dark, .dark *));

@theme inline {
  --font-sans: var(--font-geist);   /* design tokens live here in v4 */
}
```

**Usage** — utilities in markup, with `dark:` variants for dark mode and responsive prefixes (`md:`) for
breakpoints:

```tsx
<div className="flex flex-col gap-4 p-6 bg-white text-gray-900 dark:bg-gray-950 dark:text-gray-100 md:flex-row">
  …
</div>
```

> **In this repo:** dark mode is toggled by adding/removing a `.dark` class on the root (managed by a
> `ThemeProvider` that reads `matchMedia('(prefers-color-scheme: dark)')`). The `@variant dark` line above is the
> v4 way to bind `dark:` utilities to that class — a common gotcha when migrating from v3's `darkMode: 'class'`.

### 6.4 State management (Redux Toolkit)

**What & why.** When many components share and mutate the same data, prop-drilling and scattered `useState`
become unmanageable. Redux Toolkit (RTK) centralizes shared state into a single store composed of **slices**.
Each slice owns a piece of state plus the reducers that change it. Components read with `useSelector` and write
with `useDispatch`.

**Store** = a map of slice reducers:

```ts
// stores/index.ts
import { configureStore } from "@reduxjs/toolkit";
import { connectionSlice } from "./connectionSlice";
import { uiSlice } from "./uiSlice";

export const store = configureStore({
  reducer: {
    connections: connectionSlice.reducer,
    ui: uiSlice.reducer,
  },
});

export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;
```

**Slice** = state + reducers + actions, written with "mutating" syntax (RTK uses Immer to keep it immutable):

```ts
// stores/connectionSlice.ts
import { createSlice, createSelector, type PayloadAction } from "@reduxjs/toolkit";
import type { RootState } from "./index";

interface Filters { company: string; favoritesOnly: boolean }
interface State { items: Item[]; favorites: string[]; query: string; filters: Filters }

const initialState: State = { items: [], favorites: [], query: "", filters: { company: "", favoritesOnly: false } };

export const connectionSlice = createSlice({
  name: "connections",
  initialState,
  reducers: {
    setItems(state, action: PayloadAction<Item[]>) { state.items = action.payload; },
    toggleFavorite(state, action: PayloadAction<string>) {
      const i = state.favorites.indexOf(action.payload);
      if (i === -1) state.favorites.push(action.payload); else state.favorites.splice(i, 1);
    },
    setQuery(state, action: PayloadAction<string>) { state.query = action.payload; },
  },
});

export const { setItems, toggleFavorite, setQuery } = connectionSlice.actions;

// --- Selectors live at the bottom of the slice file ---
const selectItems = (s: RootState) => s.connections.items;
const selectQuery = (s: RootState) => s.connections.query;

// createSelector MEMOIZES derived data: it only recomputes when its inputs change,
// avoiding wasted filtering work on every render.
export const selectFiltered = createSelector(
  selectItems, selectQuery,
  (items, query) => items.filter(i => i.name.toLowerCase().includes(query.toLowerCase())),
);
```

**Using it in a component:**

```tsx
"use client";
import { useSelector, useDispatch } from "react-redux";
import { selectFiltered, setQuery } from "@/stores/connectionSlice";

export function Search() {
  const results = useSelector(selectFiltered);
  const dispatch = useDispatch();
  return (
    <>
      <input onChange={e => dispatch(setQuery(e.target.value))} />
      <ul>{results.map(r => <li key={r.id}>{r.name}</li>)}</ul>
    </>
  );
}
```

**Persistence pattern.** Subscribe to the store and mirror state to `localStorage`; load it back on startup.
A subtle but important rule: *when the user is authenticated, the server is the source of truth*, so you persist
only UI preferences locally — not data the server already owns.

```ts
const PERSIST_KEY = "app_state";
export function saveState(state: RootState) {
  const payload: Record<string, unknown> = { ui: state.ui };          // always persist UI prefs
  if (!isAuthenticated()) payload.connections = state.connections;    // persist data only for guests
  localStorage.setItem(PERSIST_KEY, JSON.stringify(payload));
}
```

> **In this repo:** the store has six slices (`connections`, `relationships`, `notes`, `followUps`, `auth`,
> `ui`). Selectors sit at the bottom of each slice file; `createSelector` powers the filtered-connections list.
> Persistence is gated on auth exactly as above, with a 1-second debounced sync to the server for logged-in users.

### 6.5 Forms (React Hook Form + Zod)

**What & why.** React Hook Form (RHF) manages form state with minimal re-renders. Zod defines a schema once and
gives you *both* runtime validation *and* a static TypeScript type. `@hookform/resolvers` glues them together.

```tsx
"use client";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";

const schema = z.object({
  email: z.string().email("Enter a valid email"),
  password: z.string().min(8, "At least 8 characters"),
});
type FormValues = z.infer<typeof schema>;   // { email: string; password: string }

export function LoginForm() {
  const { register, handleSubmit, formState: { errors } } = useForm<FormValues>({
    resolver: zodResolver(schema),
  });

  const onSubmit = async (values: FormValues) => {
    await fetch("/api/auth/login", { method: "POST", body: JSON.stringify(values) });
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)}>
      <input type="email" {...register("email")} />
      {errors.email && <p>{errors.email.message}</p>}
      <input type="password" {...register("password")} />
      {errors.password && <p>{errors.password.message}</p>}
      <button type="submit">Sign in</button>
    </form>
  );
}
```

The beauty: the *same* Zod schema can validate the request body on the server (Section 7.5), so client and server
agree on shape by construction.

> **In this repo:** all four auth screens (login, register, forgot-password, reset-password) use this
> RHF + Zod pattern.

---

## 7. Backend

In this stack the "backend" is not a separate server — it's the set of server-side route handlers that Next.js
runs for you under `app/api/`. They share the same repo, language, and types as the frontend.

### 7.1 API route handlers

**What & why.** A `route.ts` file inside `app/api/**` exports functions named after HTTP verbs (`GET`, `POST`,
…). Next.js runs them on the server in response to requests to that path.

```ts
// app/api/things/route.ts
import { NextRequest, NextResponse } from "next/server";

export async function GET() {
  return NextResponse.json({ items: [] });
}

export async function POST(req: NextRequest) {
  const body = await req.json();
  // …persist…
  return NextResponse.json({ ok: true }, { status: 201 });
}
```

A full handler typically does four things in order: **authenticate → validate → do work in the DB → respond.**
Here is a real one (annotated):

```ts
// app/api/connections/route.ts
export const dynamic = "force-dynamic";        // never cache; always run on the server

import { NextRequest, NextResponse } from "next/server";
import { requireAuth } from "@/lib/requireAuth";
import { getDb } from "@/lib/db";
import { z } from "zod";

const bodySchema = z.array(z.object({
  name: z.string().max(200),
  company: z.string().max(200),
  personKey: z.string().max(300),
})).max(20000);

export async function POST(req: NextRequest) {
  // 1) authenticate (throws a 401 Response if missing/invalid)
  let payload;
  try { payload = await requireAuth(req); } catch (res) { return res as Response; }

  // 2) validate the untrusted body
  const parsed = bodySchema.safeParse(await req.json().catch(() => null));
  if (!parsed.success) return NextResponse.json({ error: "Invalid input" }, { status: 400 });

  // 3) do the work inside a transaction (all-or-nothing)
  const db = getDb();
  db.transaction(() => {
    db.prepare("DELETE FROM connections WHERE user_id = ?").run(payload.userId);
    const insert = db.prepare("INSERT INTO connections (user_id, name, company, person_key) VALUES (?,?,?,?)");
    for (const c of parsed.data) insert.run(payload.userId, c.name, c.company, c.personKey);
  })();

  // 4) respond
  return NextResponse.json({ ok: true });
}
```

### 7.2 Database (SQLite via better-sqlite3)

**What & why.** `better-sqlite3` is a synchronous, embedded SQLite driver — the entire database is a single file
on disk, with no separate server to run. It's ideal for getting a real relational backend working immediately;
you can migrate to Postgres later without changing your API shape.

**Singleton + schema-on-init.** Create the connection once per process and create tables if they don't exist:

```ts
// lib/db.ts
import Database from "better-sqlite3";
import path from "path";
import fs from "fs";

const DB_PATH = path.join(process.cwd(), "data", "app.db");
const globalForDb = globalThis as unknown as { db?: Database.Database };

function createDb() {
  fs.mkdirSync(path.dirname(DB_PATH), { recursive: true });
  const db = new Database(DB_PATH);
  db.pragma("journal_mode = WAL");   // allow concurrent reads while writing
  db.pragma("foreign_keys = ON");    // enforce referential integrity

  db.exec(`
    CREATE TABLE IF NOT EXISTS users (
      id            INTEGER PRIMARY KEY AUTOINCREMENT,
      email         TEXT UNIQUE NOT NULL,
      password_hash TEXT NOT NULL,
      created_at    INTEGER NOT NULL DEFAULT (unixepoch())
    );
    CREATE TABLE IF NOT EXISTS connections (
      id      INTEGER PRIMARY KEY AUTOINCREMENT,
      user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
      name    TEXT NOT NULL
    );
  `);
  return db;
}

export function getDb() {
  if (!globalForDb.db) globalForDb.db = createDb();   // reused across hot-reloads & requests
  return globalForDb.db;
}
```

**Querying** uses prepared statements (which also prevent SQL injection):

```ts
const db = getDb();
const user = db.prepare("SELECT * FROM users WHERE email = ?").get(email);     // one row
const rows = db.prepare("SELECT * FROM connections WHERE user_id = ?").all(id); // many rows
db.prepare("INSERT INTO users (email, password_hash) VALUES (?, ?)").run(email, hash);
```

Key practices baked into the pattern: **scope every row by `user_id`** (multi-tenant isolation),
**use `ON DELETE CASCADE`** so deleting a user cleans up their data, and **run multi-statement writes in a
`db.transaction(...)`** so they're atomic.

> **In this repo:** the schema has 11 tables (users, connections, relationships, custom_types, notes, favorites,
> archives, follow_ups, shared_graphs, user_snapshots, password_reset_tokens), all `user_id`-scoped, with a
> guarded column migration (adds `is_admin` if missing) and optional admin seeding from `ADMIN_EMAIL` /
> `ADMIN_PASSWORD` env vars. The DB file lives in `data/` and is **gitignored**.

### 7.3 Authentication (JWT + bcrypt)

**What & why.** Two separate concerns:
- **Password storage** — never store raw passwords. Hash them with **bcrypt**, a deliberately slow, salted
  algorithm.
- **Sessions** — issue a **JWT** (JSON Web Token) on login: a signed, tamper-evident token the client returns on
  each request. The server verifies the signature instead of looking up a session in a database (stateless auth).

```ts
// hashing (registration / login)
import bcrypt from "bcryptjs";
const hash = await bcrypt.hash(plainPassword, 12);     // store `hash`
const ok   = await bcrypt.compare(plainPassword, hash); // true/false at login
```

```ts
// lib/jwt.ts — sign on login, verify on each request
import jwt from "jsonwebtoken";

export interface JWTPayload { userId: number; email: string; isAdmin: boolean }

function getSecret(): string {
  const s = process.env.JWT_SECRET;
  if (!s) throw new Error("JWT_SECRET is not set");   // fail loud if misconfigured
  return s;
}

export function signToken(p: JWTPayload): string {
  return jwt.sign(p, getSecret(), { expiresIn: "7d" });
}
export function verifyToken(token: string): JWTPayload {
  return jwt.verify(token, getSecret()) as JWTPayload;
}
```

**Reading auth in a handler.** A small helper accepts the token from either an `Authorization: Bearer …` header
*or* an httpOnly cookie, and throws a ready-made `401` response if it's missing/invalid:

```ts
// lib/requireAuth.ts (abridged)
export async function requireAuth(req: NextRequest): Promise<JWTPayload> {
  const header = req.headers.get("authorization") ?? "";
  const token = header.startsWith("Bearer ") ? header.slice(7) : req.cookies.get("nm_token")?.value;
  if (!token) throw new Response(JSON.stringify({ error: "Unauthorized" }), { status: 401 });
  try { return verifyToken(token); }
  catch { throw new Response(JSON.stringify({ error: "Invalid or expired token" }), { status: 401 }); }
}

export async function requireAdmin(req: NextRequest) {
  const payload = await requireAuth(req);
  if (!payload.isAdmin) throw NextResponse.json({ error: "Forbidden" }, { status: 403 });
  return payload;
}
```

> **Why two JWT libraries?** `jsonwebtoken` is full-featured but depends on Node APIs, so it's used inside API
> routes (Node runtime). Next.js **middleware** runs on the lighter *Edge* runtime, which needs the
> Web-Crypto-based `jose` instead. In this repo `lib/jwt.ts` (jsonwebtoken) handles signing/verifying in routes,
> while `lib/jwt-edge.ts` (jose) only *decodes* the token in middleware for routing decisions.

### 7.4 Route protection (middleware)

**What & why.** `middleware.ts` at the project root runs *before* a request reaches a page — perfect for
redirecting unauthenticated users away from protected pages. **Important:** middleware is for *routing*, not
security. It decodes the token to decide where to send the browser; the real cryptographic check still happens in
every API route (Section 7.3).

```ts
// middleware.ts
import { NextRequest, NextResponse } from "next/server";
import { decodeTokenPayload, COOKIE_NAME } from "@/lib/jwt-edge";

const PROTECTED = ["/search", "/graph", "/profile"];
const AUTH_ONLY = ["/login", "/register"];   // send logged-in users away from these

export function middleware(req: NextRequest) {
  const { pathname } = req.nextUrl;
  const token = req.cookies.get(COOKIE_NAME)?.value ?? null;
  const payload = token ? decodeTokenPayload(token) : null;  // decode only — not verify

  if (PROTECTED.some(p => pathname.startsWith(p)) && !payload) {
    const url = req.nextUrl.clone(); url.pathname = "/login"; url.searchParams.set("from", pathname);
    return NextResponse.redirect(url);
  }
  if (AUTH_ONLY.some(p => pathname.startsWith(p)) && payload) {
    const url = req.nextUrl.clone(); url.pathname = "/search";
    return NextResponse.redirect(url);
  }
  return NextResponse.next();
}

// Only run middleware on these paths (keeps it off static assets/API)
export const config = {
  matcher: ["/search/:path*", "/graph/:path*", "/profile/:path*", "/login", "/register", "/admin/:path*"],
};
```

> **In this repo:** middleware also gates `/admin` routes on an `isAdmin` claim and supports a non-sensitive
> client-set fallback cookie (`nm_authed`) for environments where the httpOnly cookie can't be stored.

### 7.5 Input validation, rate limiting & transactional email

**Validation (Zod).** Re-validate *every* request body on the server, even if the client already did — never
trust the network. (`safeParse` returns success/failure instead of throwing.)

```ts
const schema = z.object({ email: z.string().email(), password: z.string().min(8) });
const parsed = schema.safeParse(await req.json().catch(() => null));
if (!parsed.success) return NextResponse.json({ error: "Invalid input" }, { status: 400 });
```

**Rate limiting.** Throttle sensitive endpoints (login, forgot-password) by client IP to blunt brute-force and
abuse. A simple in-memory limiter is enough for a single instance; use a shared store (e.g. Redis) when you scale
horizontally.

**Transactional email (Resend).** For flows like password reset, generate a cryptographically random token,
store only its **hash** in the DB with a short expiry, and email the *raw* token in a link. When the user clicks
through, hash the incoming token and compare. This way a database leak never exposes usable reset links.

```ts
import { Resend } from "resend";
const resend = new Resend(process.env.RESEND_API_KEY);
await resend.emails.send({
  from: "noreply@yourapp.com",
  to: user.email,
  subject: "Reset your password",
  html: `<a href="https://yourapp.com/reset-password?token=${rawToken}">Reset</a>`,
});
```

> **In this repo:** the password-reset flow stores a SHA-256 hash of the token with a 1-hour TTL, rate-limits the
> request endpoint by IP, and falls back to logging the link to the console in development if no `RESEND_API_KEY`
> is configured — so you can test without sending real mail.

### 7.6 Security headers

Set defense-in-depth HTTP headers in `next.config.ts`. A Content-Security-Policy, `X-Frame-Options`,
`Strict-Transport-Security`, etc., are cheap and meaningfully reduce attack surface.

```ts
// next.config.ts (excerpt)
const nextConfig = {
  async headers() {
    if (process.env.NODE_ENV === "development") return [];   // relax in dev
    return [{
      source: "/(.*)",
      headers: [
        { key: "X-Frame-Options", value: "SAMEORIGIN" },
        { key: "X-Content-Type-Options", value: "nosniff" },
        { key: "Referrer-Policy", value: "strict-origin-when-cross-origin" },
        { key: "Strict-Transport-Security", value: "max-age=63072000; includeSubDomains; preload" },
        { key: "Content-Security-Policy", value: "default-src 'self'; script-src 'self' 'unsafe-inline'" },
      ],
    }];
  },
};
export default nextConfig;
```

---

## 8. Docker

> **Teach + reality check.** This section shows the *standard* way to containerize a Next.js app. The reference
> repo does **not** yet do this fully — see the callout at the end for what it actually has and how to finish it.

**What & why.** Docker packages your app and its exact runtime into an image that runs identically on any
machine. Docker Compose orchestrates multiple containers (e.g. app + database) for local development.

**Multi-stage `Dockerfile`** for a Next.js production build. Multi-stage keeps the final image small: install &
build in heavier stages, copy only the runtime output into a slim final image. (Pair it with
`output: "standalone"` in `next.config.ts` so Next emits a minimal self-contained server.)

```dockerfile
# 1) Install dependencies
FROM node:22-alpine AS deps
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci

# 2) Build the app
FROM node:22-alpine AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .
RUN npm run build

# 3) Minimal runtime image
FROM node:22-alpine AS runner
WORKDIR /app
ENV NODE_ENV=production
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static
COPY --from=builder /app/public ./public
EXPOSE 3000
CMD ["node", "server.js"]
```

**`.dockerignore`** (mirror your `.gitignore`) keeps build context small and secrets out of the image:

```dockerignore
node_modules
.next
.git
.env*
coverage
```

**`docker-compose.yml`** to run the app alongside a Postgres database locally:

```yaml
services:
  app:
    build: .
    ports: ["3000:3000"]
    environment:
      DATABASE_URL: postgres://app:app@db:5432/app
      JWT_SECRET: ${JWT_SECRET}      # injected from your shell / .env, never hard-coded
    depends_on: [db]
  db:
    image: postgres:16
    restart: unless-stopped
    environment:
      POSTGRES_USER: app
      POSTGRES_PASSWORD: app
      POSTGRES_DB: app
    ports: ["5432:5432"]
    volumes: ["postgres_data:/var/lib/postgresql/data"]   # data survives container restarts

volumes:
  postgres_data:
```

```bash
docker compose up --build      # start app + db
docker compose down            # stop (add -v to also wipe the volume)
```

> **In this repo:** there is a `docker-compose.yml`, but it currently defines **only a Postgres 16 service** — and
> the app doesn't use it (the app runs on embedded SQLite, Section 7.2). There is **no `Dockerfile`** and no
> `.dockerignore`. So Docker is *scaffolded but not wired in*. To complete it you would: (1) add the multi-stage
> `Dockerfile` and `.dockerignore` above, (2) add an `app` service to compose, and (3) either point the app at
> Postgres via a `DATABASE_URL` (swapping `better-sqlite3` for a Postgres client) or mount a volume for the
> SQLite file so data persists. The Postgres service is best read as a *future migration target*.

---

## 9. Testing — the TDD Workflow

The discipline: **describe behavior first, watch it fail, then make it pass.**

1. **Spec (plain English).** Write scenarios in Gherkin (`Given/When/Then`) describing the behavior and which
   components/paths to cover. These are *working documents*, not shipped code.
2. **Red.** Write unit + integration tests. Run them; confirm they fail for the right reason.
3. **Green.** Write the minimum code to pass.
4. **Refactor.** Clean up with tests as a safety net.
5. **E2E last.** Once a feature is stable, add a Playwright golden-path test.

```gherkin
# tests/specs/auth.feature  (a local working document)
Feature: Authentication
  Scenario: Login with correct credentials
    Given I have a registered account
    When I submit my email and password on /login
    Then I am redirected to /search
    And my session token is stored

## Integration Coverage
- LoginForm: submits credentials, shows error on failure, redirects on success
## E2E Coverage
- register → log out → log back in → data still present
```

The three test layers map to three tools:

### 9.1 Unit testing (Vitest)

**What & why.** Vitest is a fast, Vite-native test runner with a Jest-compatible API. Unit tests cover the things
with no UI or network: pure functions and **Redux slice logic** (dispatch an action to a real store, assert the
new state). These are the cheapest, most numerous tests.

**Config.** One file configures both unit and integration runs. `jsdom` simulates a browser DOM; `globals: true`
lets you use `describe/it/expect` without importing them; the path alias mirrors `tsconfig`.

```ts
// vitest.config.mts
import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";
import path from "path";

export default defineConfig({
  plugins: [react()],
  test: {
    environment: "jsdom",
    setupFiles: ["./tests/setup.ts"],
    globals: true,
    include: ["tests/unit/**/*.test.ts", "tests/unit/**/*.test.tsx", "tests/integration/**/*.test.tsx"],
    coverage: { provider: "v8", reporter: ["text", "json-summary"], include: ["lib/**", "stores/**", "components/**"] },
  },
  resolve: { alias: { "@": path.resolve(__dirname, ".") } },
});
```

```ts
// tests/setup.ts — runs before each test file
import "@testing-library/jest-dom";   // adds matchers like .toBeInTheDocument()
```

**Testing a Redux slice** — build a store from just that slice, dispatch, assert:

```ts
// tests/unit/connectionSlice.test.ts
import { describe, it, expect } from "vitest";
import { configureStore } from "@reduxjs/toolkit";
import { connectionSlice, setQuery, selectFiltered } from "@/stores/connectionSlice";

const makeStore = () => configureStore({ reducer: { connections: connectionSlice.reducer } });

describe("selectFiltered", () => {
  it("filters by search query (case-insensitive)", () => {
    const store = makeStore();
    store.dispatch(connectionSlice.actions.setItems([{ id: "1", name: "Alex" }, { id: "2", name: "Jordan" }]));
    store.dispatch(setQuery("ALEX"));
    const result = selectFiltered(store.getState());
    expect(result).toHaveLength(1);
    expect(result[0].name).toBe("Alex");
  });
});
```

Run them:

```bash
npm test                  # vitest run  — single pass (used by CI)
npm run test:watch        # vitest      — re-run on change while developing
npm run test:coverage     # vitest run --coverage
```

> **In this repo:** ~20 unit files cover slices (`connectionSlice`, `relationshipSlice`), pure utilities
> (`jwt`, `data`, `export`, `rateLimit`), edge/middleware logic, and graph math. Coverage is reported via the v8
> provider; the suite was deliberately grown (a commit titled *"Coverage increased 40 → 65"*).

### 9.2 Integration testing (Vitest + React Testing Library + MSW)

**What & why.** Integration tests render a real component **with its real store** and assert on what a user would
see and do. React Testing Library (RTL) encourages querying by accessible role/text (not implementation details).
Anything the component talks to over the network gets **mocked** so the test is fast and deterministic.

**Render with a Provider:**

```tsx
// tests/integration/LoginForm.test.tsx
import { describe, it, expect, beforeEach, vi } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { Provider } from "react-redux";
import { configureStore } from "@reduxjs/toolkit";
import { authSlice } from "@/stores/authSlice";
import { uiSlice } from "@/stores/uiSlice";
import { LoginForm } from "@/components/auth/LoginForm";

// Components that call the Next.js router need it mocked under jsdom:
vi.mock("next/navigation", () => ({ useSearchParams: () => ({ get: () => null }) }));

const makeStore = () => configureStore({ reducer: { auth: authSlice.reducer, ui: uiSlice.reducer } });
const renderForm = () => render(<Provider store={makeStore()}><LoginForm /></Provider>);

beforeEach(() => { vi.restoreAllMocks(); localStorage.clear(); });

it("shows a server error on failed login", async () => {
  // Mock the network call directly:
  vi.spyOn(globalThis, "fetch").mockResolvedValueOnce(
    new Response(JSON.stringify({ error: "Invalid email or password" }), { status: 401 }),
  );
  renderForm();
  fireEvent.change(screen.getByRole("textbox", { name: /email/i }), { target: { value: "a@b.com" } });
  fireEvent.submit(screen.getByRole("button", { name: /sign in/i }));
  await waitFor(() => expect(screen.getByText(/invalid email or password/i)).toBeInTheDocument());
});
```

There are **two common ways to mock the network** in integration tests — know both:

**(a) `vi.spyOn(fetch)` — quick and local.** Replace `fetch` per test with a canned `Response`. Minimal setup;
ideal when only a handful of calls matter and you want the mock visible right next to the assertion. *This is what
the reference repo uses.*

```ts
vi.spyOn(globalThis, "fetch").mockResolvedValueOnce(
  new Response(JSON.stringify({ token: "tok-abc", user: { id: 1 } }), { status: 200 }),
);
```

**(b) MSW (Mock Service Worker) — realistic and centralized.** MSW intercepts requests at the network layer using
*request handlers*, so your component code calls `fetch` exactly as in production and doesn't know it's being
mocked. Handlers are defined once and shared across all tests, which scales better as the number of endpoints
grows and lets you model a fake API faithfully (status codes, latency, conditional responses).

```ts
// tests/mocks/handlers.ts
import { http, HttpResponse } from "msw";

export const handlers = [
  http.post("/api/auth/login", async ({ request }) => {
    const { email } = (await request.json()) as { email: string };
    if (email === "bad@b.com") return HttpResponse.json({ error: "Invalid email or password" }, { status: 401 });
    return HttpResponse.json({ token: "tok-abc", user: { id: 1, email } });
  }),
];
```

```ts
// tests/mocks/server.ts
import { setupServer } from "msw/node";
import { handlers } from "./handlers";
export const server = setupServer(...handlers);
```

```ts
// add to tests/setup.ts to turn MSW on for every test
import { server } from "./mocks/server";
beforeAll(() => server.listen({ onUnhandledRequest: "error" }));
afterEach(() => server.resetHandlers());   // undo per-test overrides
afterAll(() => server.close());
```

Individual tests can still override a handler for one case (`server.use(http.post(...))`), then `resetHandlers`
restores the defaults.

> **In this repo:** MSW **is installed** (`msw ^2.14.6`) but **not currently wired in** — every integration test
> mocks the network with `vi.spyOn(globalThis, 'fetch')` as in (a). Both approaches are valid; the project chose
> the lighter one. If/when the number of endpoints or the need for shared fixtures grows, migrating to the MSW
> setup in (b) is the natural next step — the `tests/mocks/` folder is already the place for it.

> **jsdom gotchas:** jsdom implements *most* of the DOM but not everything. Browser-only APIs your components
> touch — `window.matchMedia`, `ResizeObserver`, `<canvas>` `getContext`, `window.location` assignment — must be
> stubbed in setup or per-test (e.g. `vi.fn()`), or the test will throw.

### 9.3 End-to-end testing (Playwright)

**What & why.** E2E tests are the top of the pyramid: they launch a **real browser**, start (or reuse) the
**real app**, and click through it like a user — exercising frontend, backend, and database together. They're
slow and broad, so you keep a *few* covering critical "golden paths" rather than every edge case.

**Config.** Playwright can start your dev server for you (`webServer`) and wait until it's reachable before
running:

```ts
// playwright.config.ts
import { defineConfig, devices } from "@playwright/test";

export default defineConfig({
  testDir: "./tests/e2e",
  fullyParallel: true,
  forbidOnly: !!process.env.CI,          // fail CI if a stray `test.only` is committed
  retries: process.env.CI ? 2 : 0,        // tolerate flakiness only in CI
  reporter: "html",
  use: { baseURL: "http://localhost:3000", trace: "on-first-retry" },  // record a trace to debug failures
  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"] } }],
  webServer: {
    command: "npm run dev",
    url: "http://localhost:3000",
    reuseExistingServer: !process.env.CI,  // locally reuse a running server; in CI start fresh
  },
});
```

**A golden-path spec** — note how you can run *two browser contexts* to simulate two different users/sessions:

```ts
// tests/e2e/share.spec.ts
import { test, expect } from "@playwright/test";

test("owner shares a link; a visitor sees a read-only view", async ({ page, browser }) => {
  // Owner logs in and creates a share link
  await page.goto("/login");
  await page.fill('input[type="email"]', "owner@example.com");
  await page.fill('input[type="password"]', "password123");
  await page.click("button:has-text('Sign in')");
  await page.click("button:has-text('Create share link')");
  const shareUrl = await page.locator("[data-share-url]").inputValue();

  // A separate, logged-out context opens the link
  const visitor = await browser.newContext();
  const visitorPage = await visitor.newPage();
  await visitorPage.goto(shareUrl);
  await expect(visitorPage.getByText(/read-only/i)).toBeVisible();
  await visitor.close();
});
```

```bash
npm run test:e2e                 # playwright test (headless)
npx playwright test --ui         # interactive UI mode for debugging
npx playwright install           # one-time: download browser binaries
```

> **In this repo:** Playwright runs **Chromium only**, with one golden-path spec (`graph-share.spec.ts`) that
> tests the share flow across an owner context and a visitor context. E2E runs locally via `npm run test:e2e`
> (it is intentionally *not* part of CI — see the next section).

---

## 10. CI/CD — GitHub Actions

**What & why.** Continuous Integration runs your tests and build automatically on every push and pull request, so
broken code is caught before it merges. GitHub Actions reads workflow YAML from `.github/workflows/`.

**A two-job pipeline: test, then build.** The `build` job declares `needs: test`, so it only runs if tests pass —
fail fast and cheap.

```yaml
# .github/workflows/ci.yml
name: CI

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    name: Test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: 22
          cache: npm                 # cache ~/.npm between runs for speed
      - run: npm ci                  # clean, lockfile-exact install
      - run: npm test                # vitest run (unit + integration)
        env:
          JWT_SECRET: ci-test-secret-not-used-in-unit-tests   # placeholder, not a real secret

  build:
    name: Build
    runs-on: ubuntu-latest
    needs: test                      # only build if tests pass
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: 22
          cache: npm
      - run: npm ci
      - run: npm run build           # next build — also type-checks the whole app
        env:
          JWT_SECRET: ci-build-secret-not-real
          NEXT_PUBLIC_API_BASE: http://localhost:3000
```

**Secrets — the right way.** Never commit real credentials. Inject them at runtime:
- In CI, store real values as **GitHub repository secrets** and reference them as `${{ secrets.JWT_SECRET }}`.
- Locally, keep them in a **gitignored `.env`** file.
- The placeholder strings above are intentionally fake — they exist only so the build/test process has *some*
  value present, not because they're sensitive.

> **In this repo:** the workflow is exactly the two-job test→build pipeline above, on Node 22, triggered by push
> and PR to `main`. There is **no deploy job** and **no E2E in CI** (Playwright runs locally). Natural extensions:
> add a `test:e2e` job (with `npx playwright install --with-deps`), upload the coverage/HTML reports as
> artifacts, and add a deploy job (e.g. to Vercel) gated on `needs: [test, build]`.

> ⚠️ **Workplace note (per CITY Furniture's AI Policy).** If you apply these CD/deployment practices inside CITY's
> environment, remember that **production deployments, new system integrations, and installing non-approved APIs,
> plug-ins, connectors, or standing up new GenAI software require approval via a Tech Request Form.** This guide
> is for a personal side project; adapt accordingly at work, and route policy/exception questions to the CIO or
> VP of HR.

---

## 11. Architecture Decision Records (ADRs)

**What & why.** An ADR is a short markdown file recording *one* significant technical decision and its rationale,
so a future contributor (or future you) understands *why* the code is the way it is. They're numbered
sequentially and immutable: when a decision changes, you write a new ADR and mark the old one `Superseded`.

```markdown
# ADR-007: Use SQLite (better-sqlite3) for persistence

## Status
Accepted

## Context
We need a real relational store but want zero infrastructure for local dev and early deployment.

## Decision
Use better-sqlite3 with a schema-on-init module and a singleton connection. Keep the API shape
storage-agnostic so a later move to Postgres is mechanical.

## Consequences
+ No DB server to run; the database is a single file.
+ Synchronous queries simplify handler code.
− Single-writer; horizontal scaling will require migrating to Postgres (tracked as a future ADR).
```

**Write or update an ADR when:** adding a dependency, changing the state shape (new slice/major selector),
changing a routing convention, or making any choice that would surprise a newcomer.

> **In this repo:** ADRs live in `docs/adr/ADR-NNN-<slug>.md` and are **gitignored** as local working documents
> (same rationale as the Gherkin specs).

---

## 12. Recreation Checklist

A condensed, ordered path from zero to a CI-validated full-stack app:

```bash
# 1. Environment
nvm install 22 && nvm use 22 && echo "22" > .nvmrc

# 2. Scaffold
npx create-next-app@latest my-app --typescript --eslint --app --tailwind --import-alias "@/*"
cd my-app

# 3. Version control
git init && git add . && git commit -m "Initial commit"
gh repo create my-app --private --source=. --remote=origin --push

# 4. State & forms
npm i @reduxjs/toolkit react-redux react-hook-form @hookform/resolvers zod

# 5. Backend (DB + auth + email)
npm i better-sqlite3 bcryptjs jsonwebtoken jose resend
npm i -D @types/better-sqlite3 @types/bcryptjs @types/jsonwebtoken

# 6. Testing toolchain
npm i -D vitest @vitejs/plugin-react jsdom \
        @testing-library/react @testing-library/dom @testing-library/jest-dom @testing-library/user-event \
        @vitest/coverage-v8 msw @playwright/test
npx playwright install
```

Then, per feature, follow the loop:

1. Write the Gherkin spec (`tests/specs/<feature>.feature`).
2. Write failing unit + integration tests (`tests/unit`, `tests/integration`). Run `npm test` → **Red**.
3. Implement the slice / component / API route until **Green**; refactor.
4. Once stable, add a Playwright golden-path spec (`tests/e2e`).
5. Commit, push, open a PR → GitHub Actions runs test + build.
6. Record any notable decision as an ADR.

---

## 13. Appendix — Dependencies & Command Cheat-Sheet

### Runtime dependencies

| Package | Version | Why |
|---|---|---|
| `next` | `16.2.6` | Framework (routing, SSR, API, bundling) |
| `react`, `react-dom` | `19.2.4` | UI library |
| `@reduxjs/toolkit` | `^2.12.0` | Client state (slices, store, selectors) |
| `react-redux` | `^9.3.0` | React bindings for Redux |
| `react-hook-form` | `^7.77.0` | Form state management |
| `@hookform/resolvers` | `^5.4.0` | Bridges RHF with Zod |
| `zod` | `^4.4.3` | Schema validation + inferred types |
| `better-sqlite3` | `^12.10.0` | Embedded SQLite database driver |
| `bcryptjs` | `^3.0.3` | Password hashing |
| `jsonwebtoken` | `^9.0.3` | JWT sign/verify (Node runtime) |
| `jose` | `^6.2.3` | JWT decode (Edge runtime / middleware) |
| `resend` | `^6.12.4` | Transactional email |

### Dev / tooling dependencies

| Package | Version | Why |
|---|---|---|
| `typescript` | `^5` | Static typing |
| `tailwindcss`, `@tailwindcss/postcss` | `^4` | Utility-first CSS (v4, PostCSS plugin) |
| `eslint`, `eslint-config-next` | `^9`, `16.2.6` | Linting (flat config) |
| `vitest` | `^4.1.8` | Test runner |
| `@vitejs/plugin-react` | `^6.0.2` | React support in Vitest |
| `@vitest/coverage-v8` | `^4.1.8` | Coverage reporting |
| `jsdom` | `^29.1.1` | DOM simulation for tests |
| `@testing-library/react` | `^16.3.2` | Render/query components |
| `@testing-library/dom` | `^10.4.1` | DOM queries (peer) |
| `@testing-library/jest-dom` | `^6.9.1` | Extra DOM matchers |
| `@testing-library/user-event` | `^14.6.1` | Realistic user interactions |
| `msw` | `^2.14.6` | Network mocking (handler-based) |
| `@playwright/test` | `^1.60.0` | End-to-end browser testing |

### Command cheat-sheet

| Command | What it does |
|---|---|
| `npm run dev` | Start the dev server at `http://localhost:3000` (use `-p 3002` if the port is taken) |
| `npm run build` | Production build **+ full TypeScript type-check** |
| `npm start` | Run the production build |
| `npm run lint` | Run ESLint |
| `npm test` | Run unit + integration tests once (what CI runs) |
| `npm run test:watch` | Re-run tests on file change |
| `npm run test:coverage` | Tests with a coverage report |
| `npm run test:e2e` | Run Playwright E2E tests |
| `docker compose up --build` | Build & run app + services in containers |

### Environment variables

| Variable | Used by | Notes |
|---|---|---|
| `JWT_SECRET` | auth (sign/verify tokens) | **required**; keep in `.env` / GitHub Secrets, never commit |
| `RESEND_API_KEY` | email | optional; falls back to console logging in dev |
| `ADMIN_EMAIL`, `ADMIN_PASSWORD` | DB seeding | optional; seed an admin account on first run |
| `NEXT_PUBLIC_API_BASE` | client | the `NEXT_PUBLIC_` prefix exposes a var to the browser |

---

*End of playbook. This document describes a general, reusable stack and workflow; the "In this repo" callouts map
each idea to one real implementation so you can see theory and practice side by side.*
