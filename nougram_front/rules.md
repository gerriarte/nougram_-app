# NOUGRAM DESIGN SYSTEM RULES (COLOMBIA EDITION)

## 1. Visual Hierarchy & Tokens

- **Primary Color:** #3B82F6 (Action buttons, primary links).
- **Success Color:** #10B981 (Profitable margins, successful saves).
- **Warning Color:** #F59E0B (Low margins, missing tax info).
- **Critical Color:** #DC2626 (Negative margins, data errors).
- **Typography:** Use 'Inter' or system sans-serif. Titles: Semibold. Body: Regular.
- **Rounding:** Use standard `rounded-lg` (8px) for cards and `rounded-md` (6px) for buttons.

## 2. Layout & Spacing (8pt Grid System)

- All spacing must be multiples of 4px or 8px (Tailwind standard: p-2, p-4, p-8, gap-4, etc.).
- **Container:** Max-width 1280px for desktop, full-width with 16px padding for mobile.
- **Cards:** White background, thin border (#E5E7EB), subtle shadow (`shadow-sm`).

## 3. Component Consistency

- **Buttons:** - Primary: Solid background, white text.
  - Secondary: Ghost or Outline.
  - Destructive: Solid red for delete/critical warnings.
- **Inputs:**
  - Every currency input MUST be right-aligned and prefixed with "$".
  - Always use 'COP' as the default suffix for Colombian users.
- **Tables:** Compact style, zebra-striping (#F9FAFB), numbers always right-aligned.

## 4. Financial Feedback Logic (CRITICAL)

- **Margin Badge Color Rule:**
  - IF margin >= 30%: Text/Background Green.
  - IF margin < 30% AND >= 20%: Text/Background Amber.
  - IF margin < 20%: Text/Background Red + Alert Icon.
- **Currency Formatting:** Use `Intl.NumberFormat('es-CO')` for all displays.
  - Example: $1.000.000,00 (or $1,000,000.00 depending on preference, stay consistent).

## 5. Accessibility (WCAG)

- Minimum contrast ratio 4.5:1.
- All interactive elements must have a visible :focus state.
- Form labels must always be present (avoid placeholder-only forms).

# Nougram Frontend Rules

## Core Principle: "The View Does Not Think"

[cite_start]Based on the architectural principle that "La vista no piensa, solo muestra". Keep UI components clean of business or complex data logic.

## Directory Structure (Adaptive)

- `src/components/`: Pure UI components (Views).
- [cite_start]`src/services/`: API calls and data transformation (similar to Backend Services).
- `src/hooks/`: Business logic and state management orchestration.
- [cite_start]`src/models/`: Type definitions and interfaces (Domain entities).

## Naming & Standards

- Follow `PascalCase` for Components and `camelCase` for functions/files.
- [cite_start]**Low Coupling**: Components should not depend directly on infrastructure or complex API logic; use services as intermediaries.

## Execution Flow

1. Component triggers an action.
2. Hook/Service processes the business logic or API call.
3. [cite_start]Component receives the updated state and renders.
