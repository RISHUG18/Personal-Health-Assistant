# Frontend Component Documentation

**Version:** 1.0.0  
**Last Updated:** 2025-03-02  
**Framework:** Next.js 16, React 18, TypeScript, Tailwind CSS v4

## 📋 Table of Contents

1. [UI Components](#ui-components)
   - Error Handling Components
   - Loading States
   - Empty States
   - Design System
2. [Async Hooks](#async-hooks)
3. [Alert & Error Utilities](#alert--error-utilities)
4. [Usage Examples](#usage-examples)
5. [Best Practices](#best-practices)

---

## UI Components

All UI components are located in `src/frontend/components/ui/`.

### Error Handling Components

#### ErrorBoundary

**File:** `ErrorBoundary.tsx`  
**Type:** React Class Component  
**Purpose:** Catches JavaScript errors in child components

**Props:**
```typescript
interface ErrorBoundaryProps {
  children: React.ReactNode;
  fallback?: React.ReactNode;  // Optional custom fallback UI
}
```

**Usage:**
```tsx
import { ErrorBoundary } from "@/components/ui/ErrorBoundary";

export default function Page() {
  return (
    <ErrorBoundary>
      <ReportsList />  {/* Errors here are caught */}
    </ErrorBoundary>
  );
}
```

**Features:**
- 🛡️ Catches errors in entire subtree
- 🎨 Displays user-friendly fallback UI
- 🐛 Development mode shows error stack
- 🔄 Reset button to retry
- 🏠 Home button navigation

**States:**
- Normal: Renders children unmolested
- Error: Displays error UI with recovery options
- Development: Shows error message and stack trace

**Auto-reset:** No (manual "Try again" button)

---

#### ErrorFallback

**File:** `ErrorFallback.tsx`  
**Type:** Functional Component  
**Purpose:** Display formatted error messages with actions

**Props:**
```typescript
interface ErrorFallbackProps {
  title?: string;                          // Error heading
  message: string;                         // Error description
  icon?: string;                           // Emoji or icon (default: "⚠️")
  action?: {                               // Primary CTA
    label: string;
    onClick: () => void;
  };
  secondary?: {                            // Secondary CTA
    label: string;
    onClick: () => void;
  };
  variant?: "compact" | "full";           // Layout variant (default: "full")
  className?: string;                      // Additional Tailwind classes
}
```

**Usage:**
```tsx
import { ErrorFallback } from "@/components/ui/ErrorFallback";

// Full variant (centered, prominent)
<ErrorFallback
  title="Failed to fetch reports"
  message="We couldn't load your medical reports. Please try again."
  icon="📄"
  action={{ label: "Retry", onClick: () => refetch() }}
  secondary={{ label: "Go Home", onClick: () => navigate('/') }}
/>

// Compact variant (inline, minimal)
<ErrorFallback
  message="Failed to load. Retry?"
  variant="compact"
  action={{ label: "Retry", onClick: () => retry() }}
/>
```

**Variants:**
| Variant | Use Case | Size |
|---------|----------|------|
| `full` | Page-level errors, 404s | Large, centered |
| `compact` | Inline errors in cards | Small, inline |

**Automatic Error Messages:**

Function `getErrorMessage()` maps common errors to friendly messages:

| Status | Title | Message |
|--------|-------|---------|
| 404 | Not found | The resource doesn't exist |
| 401/403 | Access denied | You don't have permission |
| 5xx | Server error | Something went wrong on our end |
| Network | Connection error | Check your internet connection |

---

### Loading State Components

#### LoadingSkeleton

**File:** `LoadingSkeleton.tsx`  
**Type:** Functional Component  
**Purpose:** Placeholder content while data loads (shimmer animation)

**Basic Skeleton:**
```typescript
interface LoadingSkeletonProps {
  width?: string;        // Tailwind width class (default: "w-full")
  height?: string;       // Tailwind height class (default: "h-4")
  className?: string;    // Additional classes
}
```

**Usage:**
```tsx
import { LoadingSkeleton } from "@/components/ui/LoadingSkeleton";

// Generic placeholder
<LoadingSkeleton width="w-48" height="h-8" />

// Multiple lines
<div className="space-y-2">
  <LoadingSkeleton height="h-3" width="w-32" />
  <LoadingSkeleton height="h-4" width="w-full" />
  <LoadingSkeleton height="h-3" width="w-48" />
</div>
```

**Pre-built Skeletons:**

| Component | Purpose |
|-----------|---------|
| `StatCardSkeleton()` | Single stat card loader |
| `CardListSkeleton({ count?: number })` | List of cards (default: 3) |
| `ReportSkeleton()` | Full report view with header, chart, stats |
| `TableSkeleton({ rows?: number })` | Data table with rows (default: 5) |
| `DashboardSkeleton()` | Complete dashboard layout |

**Usage:**
```tsx
import { DashboardSkeleton, CardListSkeleton } from "@/components/ui/LoadingSkeleton";

// Full dashboard loader
{state === 'loading' && <DashboardSkeleton />}

// Report loader
{state === 'loading' && <ReportSkeleton />}

// List loader
{state === 'loading' && <CardListSkeleton count={5} />}
```

**Animation:** All skeletons have `animate-pulse` class (Tailwind built-in shimmer)

---

### Empty State Components

#### EmptyState

**File:** `shared.tsx`  
**Type:** Functional Component  
**Purpose:** Display when no data is available

**Props:**
```typescript
interface EmptyStateProps {
  message: string;              // Main message
  icon?: React.ReactNode;       // Emoji or React element
  action?: {                    // Optional CTA
    label: string;
    onClick: () => void;
  };
  subtext?: string;             // Additional details
  variant?: "default" | "compact";  // Size variant
}
```

**Usage:**
```tsx
import { EmptyState } from "@/components/ui/shared";

// Prominent empty state with CTA
<EmptyState
  icon="📭"
  message="No reports yet"
  subtext="Upload your first medical report to get started"
  variant="default"
  action={{ 
    label: "Upload Report", 
    onClick: () => openUploadDialog() 
  }}
/>

// Compact inline empty state
<EmptyState
  icon="🔍"
  message="No alerts"
  variant="compact"
/>
```

**Variants:**
| Variant | Padding | Icon Size | Button | Use |
|---------|---------|-----------|--------|-----|
| `default` | `py-16` | Large | Full button | Page/section |
| `compact` | `py-8` | Small | Text link | Inside cards |

---

### Design System Primitives

#### Card

**Props:**
```typescript
interface CardProps {
  children: React.ReactNode;
  className?: string;
  onClick?: () => void;
}
```

**Features:**
- Slate 800 background with slate 700 border
- Rounded corners and backdrop blur
- Hover effect if `onClick` provided

**Usage:**
```tsx
<Card onClick={() => console.log('clicked')}>
  <div>Card content</div>
</Card>
```

---

#### Badge

**Props:**
```typescript
interface BadgeProps {
  children: React.ReactNode;
  variant?: "default" | "outline" | "success" | "warning" | "danger" | "info";
  className?: string;
}
```

**Variants:**
| Variant | Color | Use |
|---------|-------|-----|
| `default` | Slate | Status/tag |
| `outline` | Slate border | Secondary status |
| `success` | Green | Positive states |
| `warning` | Amber | Caution states |
| `danger` | Red | Error/alert states |
| `info` | Blue | Informational |

---

#### SeverityBadge

Shows alert severity with pulsing animation for critical:

```typescript
type Severity = "low" | "medium" | "high" | "critical";

<SeverityBadge severity="critical" />  {/* Pulsing red */}
<SeverityBadge severity="high" />      {/* Solid red */}
<SeverityBadge severity="medium" />    {/* Amber */}
<SeverityBadge severity="low" />       {/* Green */}
```

---

#### StatCard

Metric display with trend indicator:

```typescript
interface StatCardProps {
  label: string;                    // Metric name (e.g., "Heart Rate")
  value: string | number;           // Value (e.g., 72)
  sub?: string;                     // Subtext (e.g., "bpm")
  icon?: React.ReactNode;           // Lucide icon
  trend?: "up" | "down" | "neutral"; // Trend arrow
  trendBad?: boolean;               // If up=bad (e.g., for LDL)
}
```

**Usage:**
```tsx
<StatCard
  label="Cholesterol"
  value={180}
  sub="mg/dL"
  icon={<Heart size={16} />}
  trend="up"
  trendBad={true}  // Up is bad for cholesterol
/>
```

---

#### Spinner

Loading spinner:

```typescript
interface SpinnerProps {
  size?: "sm" | "md" | "lg";
}
```

**Sizes:**
- `sm`: 4x4
- `md`: 6x6 (default)
- `lg`: 8x8

---

#### AqiBadge

Air quality indicator with color-coded severity:

```tsx
<AqiBadge aqi={45} />   {/* Green - Good */}
<AqiBadge aqi={85} />   {/* Yellow - Moderate */}
<AqiBadge aqi={125} />  {/* Orange - Unhealthy (Sensitive) */}
```

---

## Async Hooks

Located in `src/frontend/lib/hooks/useAsync.ts`

### useAsync

Generic async operation hook:

```typescript
interface UseAsyncOptions {
  onSuccess?: () => void;
  onError?: (error: Error) => void;
}

function useAsync<T>(
  asyncFunction: () => Promise<T>,
  immediate?: boolean,
  options?: UseAsyncOptions
): {
  state: "idle" | "loading" | "success" | "error";
  data: T | null;
  error: Error | null;
  execute: () => Promise<T>;
}
```

**Usage:**
```tsx
const { state, data, error, execute } = useAsync(
  async () => {
    const res = await fetch('/api/reports');
    return res.json();
  },
  false  // Don't fetch immediately
);

// Manual trigger
<button onClick={execute}>Fetch Reports</button>

// Or immediate fetch
const { state, data } = useAsync(
  () => fetchReports(),
  true  // Fetch on mount
);
```

---

### useFetch

Convenience hook for GET requests:

```typescript
function useFetch<T>(
  url: string,
  options?: UseAsyncOptions
): {
  state: AsyncState;
  data: T | null;
  error: Error | null;
  refetch: () => Promise<T>;
}
```

**Usage:**
```tsx
const { state, data, refetch } = useFetch<ReportData>("/api/reports");

return (
  <>
    {state === 'loading' && <Spinner />}
    {state === 'error' && <ErrorFallback message={error?.message} action={{ label: "Retry", onClick: refetch }} />}
    {state === 'success' && <Reports data={data} />}
  </>
);
```

---

### useApiCall

Mutation hook for POST/PUT/DELETE:

```typescript
function useApiCall<T, R = void>(
  apiFunction: (payload: T) => Promise<R>,
  options?: UseAsyncOptions
): {
  state: AsyncState;
  data: R | null;
  error: Error | null;
  mutate: (payload: T) => Promise<R>;
}
```

**Usage:**
```tsx
const { state, error, mutate } = useApiCall(
  (data) => fetch("/api/submit", {
    method: "POST",
    body: JSON.stringify(data)
  }).then(r => r.json())
);

const handleSubmit = async (formData) => {
  try {
    await mutate(formData);
    showAlert("success", "Submitted!");
  } catch (err) {
    console.error(err);
  }
};
```

---

## Alert & Error Utilities

Located in `src/frontend/lib/hooks/useAlert.ts`

### useToastAlert

Toast notification system:

```typescript
type AlertType = "success" | "error" | "warning" | "info";

function useToastAlert(): {
  alerts: Alert[];
  showAlert: (type: AlertType, title: string, message: string, duration?: number) => string;
  removeAlert: (id: string) => void;
}
```

**Usage:**
```tsx
const { showAlert } = useToastAlert();

// Success notification (auto-dismiss after 5s)
showAlert("success", "Data Saved", "Your changes have been saved");

// Error with custom timeout
showAlert("error", "Upload Failed", "File is too large", 10000);

// Manual removal
const alertId = showAlert("info", "Processing", "Please wait...", 0);
setTimeout(() => removeAlert(alertId), 3000);
```

---

### handleApiError

Converts API errors to user-friendly messages:

```typescript
function handleApiError(error: unknown): {
  title: string;
  message: string;
  severity: "info" | "warning" | "error";
}
```

**Recognized Errors:**

| Status | Title | Severity |
|--------|-------|----------|
| 404 | Not found | info |
| 401/403 | Access denied | warning |
| 422 | Invalid data | warning |
| 429 | Too many requests | warning |
| 5xx | Server error | error |
| Network | Connection error | warning |

**Usage:**
```tsx
try {
  await submitData(data);
} catch (error) {
  const { title, message, severity } = handleApiError(error);
  showAlert(severity === 'error' ? 'error' : 'warning', title, message);
}
```

---

### ApiError

Custom error class:

```typescript
class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
    public data?: unknown
  ) {}
}
```

---

## Usage Examples

### Complete Data Fetching Flow

```tsx
import { useAsync } from "@/lib/hooks/useAsync";
import { ErrorBoundary } from "@/components/ui/ErrorBoundary";
import { ErrorFallback } from "@/components/ui/ErrorFallback";
import { DashboardSkeleton } from "@/components/ui/LoadingSkeleton";
import { EmptyState } from "@/components/ui/shared";

function ReportsList() {
  const { state, data, error, execute } = useAsync(
    async () => {
      const res = await fetch('/api/reports');
      if (!res.ok) throw new Error(`${res.status}`);
      return res.json();
    },
    true  // Fetch on mount
  );

  // Loading state
  if (state === 'loading') {
    return <DashboardSkeleton />;
  }

  // Error state
  if (state === 'error') {
    return (
      <ErrorFallback
        title="Failed to load reports"
        message={error?.message || "Unknown error"}
        action={{ label: "Retry", onClick: execute }}
      />
    );
  }

  // Empty state
  if (!data?.length) {
    return (
      <EmptyState
        icon="📄"
        message="No reports found"
        action={{
          label: "Upload First Report",
          onClick: () => navigate('/upload')
        }}
      />
    );
  }

  // Success state
  return (
    <div className="grid gap-4">
      {data.map(report => (
        <ReportCard key={report.id} report={report} />
      ))}
    </div>
  );
}

export default function Page() {
  return (
    <ErrorBoundary>
      <ReportsList />
    </ErrorBoundary>
  );
}
```

---

### Form Submission with Error Handling

```tsx
import { useApiCall, handleApiError, useToastAlert } from "@/lib/hooks";

function SubmitReportForm() {
  const { showAlert } = useToastAlert();
  const { state, mutate } = useApiCall(
    (formData) => fetch("/api/reports/upload", {
      method: "POST",
      body: formData  // FormData for file upload
    }).then(r => {
      if (!r.ok) throw new Error(`${r.status}`);
      return r.json();
    })
  );

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const formData = new FormData(e.currentTarget);

    try {
      const result = await mutate(formData);
      showAlert("success", "Report Uploaded", "Your report is being processed");
      reset();
    } catch (error) {
      const { title, message } = handleApiError(error);
      showAlert("error", title, message);
    }
  };

  return (
    <form onSubmit={handleSubmit}>
      <input type="file" name="file" required />
      <button disabled={state === 'loading'}>
        {state === 'loading' ? 'Uploading...' : 'Upload'}
      </button>
    </form>
  );
}
```

---

## Best Practices

### 1. Always Wrap Route Components with ErrorBoundary

```tsx
// ✅ Good
export default function Page() {
  return (
    <ErrorBoundary>
      <YourContent />
    </ErrorBoundary>
  );
}

// ❌ Avoid
export default function Page() {
  return <YourContent />;
}
```

### 2. Use Proper Loading States

```tsx
// ✅ Good - Shows appropriate placeholder
if (state === 'loading') return <DashboardSkeleton />;

// ⚠️ Acceptable - Simple spinner
if (state === 'loading') return <Spinner />;

// ❌ Avoid - No feedback
if (state === 'loading') return null;
```

### 3. Provide Error Recovery

```tsx
// ✅ Good - User can retry
<ErrorFallback
  message={error?.message}
  action={{ label: "Retry", onClick: refetch }}
/>

// ❌ Avoid - Dead end
<ErrorFallback message="An error occurred" />
```

### 4. Show EmptyState vs Error

```tsx
// ✅ Correct
if (state === 'empty') return <EmptyState />
if (state === 'error') return <ErrorFallback />

// ❌ Confusing - mixing empty with error
if (!data) return <ErrorFallback message="No data" />
```

### 5. Handle Network Errors Gracefully

```tsx
// ✅ Good
try {
  await submitData(data);
} catch (error) {
  const { title, message } = handleApiError(error);
  showAlert('error', title, message);
}

// ❌ Avoid - Raw error message
} catch (error) {
  showAlert('error', 'Error', error.toString());
}
```

---

## Component Inventory

**Total Components:** 15+

| Category | Count | Components |
|----------|-------|-----------|
| Error Handling | 2 | ErrorBoundary, ErrorFallback |
| Loading | 6 | LoadingSkeleton + 5 presets |
| Empty State | 1 | EmptyState |
| Design System | 7 | Card, Badge, SeverityBadge, StatCard, AqiBadge, Section, Spinner |
| Hooks | 5 | useAsync, useFetch, useApiCall, useToastAlert, handleApiError |

---

**Icon Library:** [Lucide React](https://lucide.dev)  
**UI Framework:** [Radix UI](https://www.radix-ui.com)  
**Styling:** [Tailwind CSS v4](https://tailwindcss.com)  

---

**Questions?** Check the main [README.md](../README.md) for setup instructions and development tips.
