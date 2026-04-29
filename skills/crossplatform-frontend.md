---
name: crossplatform-frontend
description: "Skill for building the AI-Психолог frontend — web-first approach with React/Next.js, then wrapping for desktop (Electron/Tauri) and mobile (Capacitor/PWA). Use when designing UI components, chat interface, onboarding screens, breathing exercise timers, crisis contact screens, or discussing deployment to multiple platforms. Trigger on: frontend, UI, interface, React, Next.js, Electron, mobile app, responsive, chat design, button layout."
---

# Cross-Platform Frontend: Веб → Десктоп → Мобильные

## Strategy: Web-First, Then Wrap
1. Build web app with Next.js (React + SSR + API routes)
2. Desktop: Electron (Windows + macOS) or Tauri (lighter, Rust-based)
3. Mobile: Capacitor (wraps web into native iOS/Android) or PWA

## Why This Order
- One codebase serves all platforms
- Web is fastest to prototype and deploy
- Electron/Tauri wrap the same web code with native window
- Capacitor wraps into App Store / Google Play
- For a non-coder using AI: maintaining one codebase is critical

## Tech Stack (Frontend)
- **Framework**: Next.js 14+ (App Router)
- **Language**: TypeScript (AI writes, user reviews)
- **UI Library**: shadcn/ui + Tailwind CSS (fast, accessible, consistent)
- **State**: Zustand or React Context (simple, no Redux overhead)
- **Chat UI**: Custom component with message bubbles, buttons, timers
- **Audio**: Web Audio API for breathing exercises, ElevenLabs TTS playback
- **Offline**: Service Worker for cached exercises (СВО scenario)

## Key UI Components
1. **Chat Window**: Message bubbles (bot + user), typing indicator, button choices
2. **Crisis Banner**: Always accessible, red, one-tap to emergency contacts
3. **Breathing Timer**: Visual circle expanding/contracting with counts
4. **Onboarding Flow**: 3-step wizard (age, reason, name)
5. **Progress Dashboard**: PHQ-9/GAD-7 trends over time (Chart.js)
6. **Digital Twin Interface**: Same chat but with cloned voice toggle

## Code Quality Rules (for AI-generated code)
Since the user is not a coder, ALL code must:
- Have comments in Russian explaining what each section does
- Use descriptive variable/function names (not `x`, `temp`, `data`)
- Be modular (one component per file)
- Include error handling for every API call
- Have TypeScript types for everything (no `any`)
- Be testable (pure functions where possible)

## Desktop Wrapping
- **Electron**: `npx create-electron-app` → point to Next.js build
- **Tauri**: Lighter alternative (2-5 MB vs 100+ MB for Electron), uses Rust backend
- Recommendation: Start with Electron (more AI-code examples available), consider Tauri later

## Mobile Wrapping
- **Capacitor**: `npx cap add ios` / `npx cap add android` → wraps web view
- Native features: push notifications (follow-up check-ins), microphone (voice input)
- App Store / Google Play submission requires developer accounts ($25/$99)

## Связь с другими скиллами
- **typescript-advanced-types** → типизация всех компонентов, generics для API-клиентов
- **webapp-testing** → Playwright тесты UI (chat flow, crisis banner, breathing timer)
- **systematic-debugging** → когда UI ведёт себя не так (4-фазный дебаг)
- **user-journey-engine** → UI должен реализовывать ВСЕ пути из карты пользователя
- **elevenlabs-voice** → Web Audio API для воспроизведения TTS
- **crisis-routing** → кнопка кризиса всегда видна, номера из crisis-routing
