# Nougram Frontend

> Deprecated: este frontend está en retiro controlado.  
> Frontend principal actual: `../nougram_front`.

Next.js frontend for the Agency Profitability Platform.

## Setup

1. Install dependencies:
```bash
npm install
```

2. Start development server:
```bash
npm run dev
```

Frontend available at `http://localhost:3000`

## Project Structure

### App Router (`src/app/`)

- `(app)/` - Protected routes (requires authentication)
  - `dashboard/` - BI and AI insights
  - `projects/` - Project and quote management
  - `settings/` - Configuration (costs, team, services)

### Components

- `components/modules/` - Complex feature-specific components
- `components/ui/` - Shadcn/ui components

### Libraries

- `lib/api-client.ts` - API client configuration
- `lib/queries.ts` - TanStack Query hooks
- `lib/utils.ts` - Utility functions
- `providers/query-provider.tsx` - TanStack Query provider

## Stack

- **Framework**: Next.js 14+ (App Router)
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **Components**: Shadcn/ui
- **State Management**: TanStack Query (server) + Zustand (client)
- **Forms**: React Hook Form + Zod

## Development

### Rules

1. **Never use `any` type** - Strict TypeScript
2. **All API calls through TanStack Query** - Never fetch/axios directly
3. **No business logic in frontend** - All calculations in backend
4. **Use Shadcn/ui components** - Copy, don't install

### Creating New Pages

1. Create page in `src/app/` directory
2. Use Shadcn/ui components
3. Use TanStack Query hooks from `lib/queries.ts`
4. Handle loading and error states

### API Integration

All API calls should:
- Use TanStack Query hooks
- Handle loading states
- Handle error states
- Cache responses appropriately

Example:
```typescript
const { data, isLoading, error } = useGetServices();
```

## Environment Variables

Create `.env.local`:
```
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
```

## Building

```bash
npm run build
```

Production build creates optimized static assets.



